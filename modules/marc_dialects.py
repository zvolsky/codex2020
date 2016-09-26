# -*- coding: utf-8 -*-

from books import parse_pubyear
from c_utils import REPEATJOINER, get_publisher, get_place_publisher, make_unique, title_correction


class MarcFrom(object):
    """
        convert from Marc to (self.)properties
        must create properties for marcrec_to_fastinfo() + .isbn, .country, .pubyears

        TODO: initially made for Aleph/cz; if more systems will be implemented later,
            move specific behaviour into derived MarcFrom_AlephCz class
    """
    src_quality = 70  # default quality for z39/marc database

    def __init__(self, record):
        self.record = record

        # to make pylint happy; parse_...() will set them
        self.title_ignore_chars = 0
        self.title_indexparts = []
        self.title = self.subtitles = self.origin = self.pubplace = self.publisher = self.place_publisher = self.pubyear = self.author = self.series = ''
        self.country = self.language_orig = ''
        self.pubyears = (None, None)  # from/to
        self.languages = []
        self.publishers = []
        self.publishers_by_name = []
        self.publishers_by_place = []
        self.authorities = []
        self.authors = []
        self.subjects = []
        self.categories = []  # list of tuples: 0:$a category code, 1:$x code subdivision

        self.parse_title()
        aut_publishers = self.parse_authors()  # will call self.parse_authorities() and establish self.authorities and self.authors
        self.parse_publisher(aut_publishers)   # will eastablish self.publishers (from 110/aut_publishers or from 260/264) and .pubyear
        self.parse_lang()
        self.parse_country()
        self.parse_series()
        self.parse_subjects()  # and categories
        self.isbn = record.isbn() or ''

    def join(self, *parts):
        joined = ''
        for part in parts:
            if part:
                joined = joined.rstrip() + ' ' + part
        return joined.strip()

    def fix(self, txt, additional='.'):
        """additional: use additional='' if content usually contains abbreviations"""
        if txt:
            return txt.rstrip(':,;/= ' + additional)
        return ''

    def parse_publisher(self, aut_publishers):
        """
        will eastablish self.publisher (from aut_publishers or from 260/264) and .pubyear
        aut_publishers are from author-110
        Note: 264 field with second indicator '1' indicates publisher.
        """
        # TODO: fix .publishers[], publisher, same authors[], author
        def get_publisher_from_marc(marc_publisher):
            place = self.fix(marc_publisher['a'])
            if place and not self.pubplace:
                self.pubplace = place
            company = self.fix(marc_publisher['b'])
            if company:
                for idx, aut_publisher_row in enumerate(aut_publishers):
                    aut_publisher, used = aut_publisher_row
                    if not used and aut_publisher.lower() in company.lower():  # not very important to optimize, usually cnt is ~ 1
                        company = aut_publisher   # prefer 110, because sometimes 260/264 contains additional text like "published by.."
                        aut_publishers[idx][1] = True
                self.publishers.append(company)
                self.publishers_by_place.append(self.join(place, company))
                self.publishers_by_name.append(self.join(company, place))
            else:
                self.publishers_by_place.append(place)

            if not self.pubyear:
                pubyear = marc_publisher['c'] or ''
                if pubyear:
                    self.pubyear = pubyear
                    self.pubyears = parse_pubyear(pubyear)

        aut_publishers = [[aut_publisher, False] for aut_publisher in aut_publishers]  # False: not used for replacement
        rec = self.record
        for f in rec.get_fields('260', '264'):
            if rec['260']:
                get_publisher_from_marc(rec['260'])
            if rec['264'] and f.indicator2 == '1':
                get_publisher_from_marc(rec['264'])
        for aut_publisher, used in aut_publishers:
            if not used:
                self.publishers.append(aut_publisher)
                self.publishers_by_place.append(self.join(self.pubplace, aut_publisher))
                self.publishers_by_name.append(self.join(aut_publisher, self.pubplace))
        self.publisher = get_publisher(self.publishers)
        self.place_publisher = get_place_publisher(self.pubplace, self.publisher)

    def parse_title(self):
        def spec_append(part):
            if part[:2] == '<<' and '>>' in part:  # characters ignored for sorting
                splitted = part[2:].lstrip().split('>>', 1)
                subtitles.add(splitted[0] + splitted[1])
                indexparts.add(splitted[1].lstrip())
            else:
                subtitles.add(part)

        subtitles = set()
        indexparts = set()
        for idxt, marc_title in enumerate(self.record.get_fields('245')):  # used first 245 field only, see break cmd
            if not idxt:
                try:
                    self.title_ignore_chars = int(marc_title.indicator2)
                except:
                    self.title_ignore_chars = 0
            self.title = marc_title.value().split(' / ', 1)[0].strip()
            subtitles.add(self.title)  # add at this time and delete later after removing of duplicates
            if self.title_ignore_chars:
                indexpart = self.title[self.title_ignore_chars:].lstrip()
                if indexpart:
                    indexparts.add(indexpart)
            subval = ''
            for idx, subfld in enumerate(marc_title.subfields[::-1]):
                if idx % 2:
                    if subval and subfld in ['a', 'b', 'n', 'p']:
                        subtitles.add(subval)
                    if subfld == 'c':
                        self.origin = subval
                else:
                    subval = subfld.strip()
            break  # use first 245 field only
        for marc_title in self.record.get_fields('246'):
            if not self.title:
                subtitles.add(marc_title.value().strip())
            subval = ''
            for idx, subfld in enumerate(marc_title.subfields[::-1]):
                if idx % 2:
                    if subval and subfld in ['a', 'b', 'n', 'p']:
                        spec_append(subval)
                else:
                    subval = subfld.strip()
            mt_value = marc_title.value().strip()
            if subval != mt_value:
                spec_append(mt_value)
        self.subtitles = subtitles
        self.title_indexparts = make_unique(indexparts, safe_first=False)
                # TODO? at this time we allow indexparts with crazy_tails with the hope this will be no problem for seeking
                # crazy_tails are connectors added to the end of real data (hint: seek in the code to learn more)

    def parse_authors(self):
        """will call self.parse_authorities() and establish self.authorities and self.authors (list) + self.author (string)
        list of tuples (TODO: fix here) :
        0: author name ($a+$b+$c),
        return name of 110 author which is suitable as publisher
        """
        publishers = self.parse_authorities()
        authors = []
        for authority in self.authorities:
            if authority[5] in ('aut'):
                authors.append(authority[0])
        self.authors = authors
        self.author = REPEATJOINER.join(self.authors)
        return publishers

    def parse_authorities(self):
        """authorities (authors+...)
        list of tuples:
        0: authority name ($a+$b+$c),
        1: name $a,
        2: roman no $b,
        3: additional part of name $c,
        4: date info $d,
        5: role $4
        return name of 110 author which is suitable as publisher
        """
        def parse_one(fld, allowed_more='', get_names=False):
            return parse_common(self.record.get_fields(fld), allowed_more='', get_names=False)

        def parse_common(flds, allowed_more='', get_names=False):
            names = []
            for marc_authority in flds:
                name = self.fix(marc_authority['a'])
                if not name:
                    continue
                more1 = more2 = ''
                if 'b' in allowed_more:
                    more1 = marc_authority['b'] or ''  # roman --or-- subpart
                if 'c' in allowed_more:
                    more2 = marc_authority['c'] or ''  # additional info to the name
                date_info = marc_authority['d'] or ''
                role = marc_authority['4'] or '?'
                authorities.append((self.join(name, more1, more2).rstrip(', '), name, more1, more2, date_info, role))
                if get_names:
                    names.append(name)
            return names

        authorities = []
        parse_one('100', 'bc')  # author person
        publishers = parse_one('110', 'b', get_names=True)   # author corporation, result is suitable as publishers
        parse_one('111', 'b')   # author event/action
        parse_one('700', 'bc')  # person
        parse_one('710', 'b')   # corporation
        #parse_one('720', '')   # unsure name -- handled as addedentries
        parse_common(self.record.get_fields('711', '720', '730', '740', '752', '753', '754', '790', '791',
                        '792', '793', '796', '797', '798', '799'))    # tags from .addedentries() without 700, 710
        self.authorities = authorities
        return publishers

    def parse_lang(self):
        languages = self.record['041']
        if languages:
            self.languages = languages.get_subfields('a')
            self.language_orig = languages['h']

    def parse_country(self):
        country = self.record['044']
        if country:
            self.country = country['a']

    def parse_series(self):
        series = self.record['490']
        if series:
            self.series = self.fix(series['a'])
        #TODO: $v order(index) in series

    def parse_subjects(self):
        subjects = []
        for subject in self.record.subjects():
            subjects.append(subject['a'])
        self.subjects = subjects

        categories = []
        for category in self.record.get_fields('072'):
            categories.append((category['a'], category['x']))
        self.categories = categories


class MarcFrom_AlephCz(MarcFrom):
    """http://text.nkp.cz/o-knihovne/odborne-cinnosti/zpracovani-fondu/roztridit/stt-prehled
    TODO: MarcFrom parent class was initially made for Aleph/cz; if more systems will be implemented later,
     move specific behaviour into this derived MarcFrom_AlephCz class
    """
    pass
