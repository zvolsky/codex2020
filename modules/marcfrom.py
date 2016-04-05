# -*- coding: utf-8 -*-

class MarcFrom(object):
    def __init__(self, record):
        self.record = record

        self.title = self.publisher = self.publisher_by_name = self.pubyear = ''
        self.authorities = self.authors = []  # to make pylint happy; parse_...() will set them

        self.parse_title()
        self.parse_authors()    # will call self.parse_authorities() and establish self.authorities and self.authors
        self.parse_publisher()  # will eastablish self.publisher and .pubyear
        self.isbn = record.isbn() or ''

    def join(self, *parts):
        joined = ''
        for part in parts:
            if part:
                joined = joined.rstrip() + ' ' + part
        return joined.strip()

    def parse_publisher(self):
        """
        Note: 264 field with second indicator '1' indicates publisher.
        """
        def get_publisher(marc_publisher):
            place = marc_publisher['a']
            company = marc_publisher['b']
            self.publisher = self.join(place, company)
            self.publisher_by_name = self.join(company, name)

        for f in self.get_fields('260', '264'):
            if self['260']:
                set_publisher(self['260'])
                self.pubyear = self['260']['c'] or ''
            if self['264'] and f.indicator2 == '1':
                set_publisher(self['260'])
                self.pubyear = self['264']['c'] or ''

    def parse_title(self):
        def spec_append(part):
            if part[:2] == '<<' and '>>' in part:  # characters ignored for sorting
                splitted = part[2:].lstrip().split('>>', 1)
                parts.append(splitted[0] + splitted[1])
                parts.append(splitted[1].lstrip())
            else:
                parts.append(part)

        parts = []
        for marc_title in self.record.get_fields('245'):
            try:
                self.title_ignore_chars = int(marc_title.indicator2)
            except:
                self.title_ignore_chars = 0
            self.title = marc_title.value().strip()
            parts.append(self.title)
            if self.title_ignore_chars:
                part2 = self.title[self.title_ignore_chars:].lstrip()
                if part2:
                    parts.append(part2)
            subval = ''
            for idx, subfld in enumerate(marc_title.subfields[::-1]):
                if idx % 2:
                    if subfld in ['a', 'b', 'c', 'n', 'p']:
                        parts.append(subval)
                else:
                    subval += (' ' if subval else '') + subfld.strip()
            break  # use first 245 field only
        for marc_title in self.record.get_fields('246'):
            if not self.title:
                parts.append(marc_title.value().strip())
            subval = ''
            for idx, subfld in enumerate(marc_title.subfields[::-1]):
                if idx % 2:
                    if subfld in ['a', 'b', 'n', 'p']:
                        spec_append(subval)
                else:
                    subval += (' ' if subval else '') + subfld.strip()
            mt_value = marc_title.value().strip()
            if subval != mt_value:
                spec_append(mt_value)
        self.title_parts = parts

    def parse_authors(self):
        """will call self.parse_authorities() and establish self.authorities and self.authors
        list of tuples:
        0: author name ($a+$b+$c),
        """
        self.parse_authorities()
        authors = []
        for authority in self.authorities:
            if authority[5] in ('aut'):
                authors.append(authority[0])
        self.authors = authors

    def parse_authorities(self):
        """authorities (authors+...)
        list of tuples:
        0: authority name ($a+$b+$c),
        1: name $a,
        2: roman no $b,
        3: additional part of name $c,
        4: date info $d,
        5: role $4
        """
        def parse_one(fld, allowed_more):
            for marc_authority in self.record.get_fields('700'):
                name = marc_authority['a']
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

        authorities = []
        parse_one('100', 'bc')  # author person
        parse_one('110', 'b')   # author corporation
        parse_one('111', 'b')   # author event/action
        parse_one('700', 'bc')  # person
        parse_one('710', 'b')   # corporation
        parse_one('720', '')    # unsure name
        self.authorities = authorities

    def joined_authors(self, join_char=';'):
        """will return all authors as single string,
        authors are separated by join_char
        """
        return (join_char + ' ').join(self.authors)
