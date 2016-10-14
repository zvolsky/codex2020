# -*- coding: utf-8 -*-

"""Codex 2020 utils, completely independent on the Web2py framework
"""

from collections import defaultdict
import datetime
import hashlib
import random
import re
import string

try:
    import simplejson
except ImportError:
    from gluon.contrib import simplejson

from mzutils import hash_prepared


REPEATJOINER = '; '


def join_author(authors):
    """
    Unique way to convert tuple/list into string
    """
    return REPEATJOINER.join(authors)


def normalize_authors(authors, string_surnamed=False, string_full=False):
    """
    Args:
        authors: recommended as tuple/list, however if string is used, it is converted (allowed separators: ; or :)
        string_..: force the appropriate retval tuple item as string
    Return: tuple: (shorten to surname, full); both as list by default (but as string if forced via string_.. param)
    """
    if type(authors) not in (tuple, list):
        authors = authors.replace(':', ';').split(';')  # strip() must/will follow
    surnamed = []  # Novák == Novák,J. == Novák, Jan == Novák,Jan == Novák Jan == Novák B.J.
    full = []
    for author in authors:
        author = author.strip()
        if author:
            author = author.replace('\t', ' ')
            while '  ' in author:
                author = author.replace('  ', ' ')
            while ', ' in author:
                author = author.replace(', ', ',')
            surnamed.append(author.replace(' ', ',').split(',', 1)[0].rstrip())
            full.append(author.replace(',', ', ').rstrip())
    return join_author(surnamed) if string_surnamed else surnamed, join_author(full) if string_full else full


class Answer:
    def __init__(self, title=None, author=None, pubplace=None, publisher=None, pubyear=None,
                 subtitles=None, origin=None, keys=None):
        self.title = title
        self.author = author
        self.pubplace = pubplace
        self.publisher = publisher
        self.pubyear = pubyear
        self.subtitles = subtitles
        self.origin = origin
        self.keys = keys


def publ_fastinfo_and_hash(title, surnamed_author, author, pubplace, publisher, pubyear, subtitles=None, origin=None, keys=None):
    return (make_fastinfo(Answer(title=title, author=author, pubplace=pubplace, publisher=publisher, pubyear=pubyear,
                                 subtitles=subtitles, origin=origin, keys=keys)),
            publ_hash(title, surnamed_author, publisher, pubyear))


def publ_hash(title, author, publisher, pubyear, author_need_normalize=False):
    """
    author: prefered use is 'surname shortened'string. For anything else (list, not shortened,..) please set author_need_normalize
    publisher: publisher1 publisher2 ...
    pubyear: we use digits only
    """
    #if subtitle:
    #    title = title + subtitle  # connection not important: hash_prepared() removes all
    if author_need_normalize:
        author, _full = normalize_authors(author, string_surnamed=True)

    src = '%s|%s|%s|%s' % (hash_prepared(title, title=True), hash_prepared(author),
                           hash_prepared(publisher), filter(lambda d: d.isdigit(), pubyear))
    if type(src) == unicode:
        src = src.encode('utf-8')
    return hashlib.md5(src).hexdigest()


def make_fastinfo(rec, correct_title=False):
    """
    Args:
        title (obligatory), subtitles (list), origin, title_indexparts, title_ignore_chars,
            author,
            pubplace, publisher, pubyear, isbn,
            keys
        keys: accepts iterable (recommended) or string (use REPEATJOINER please)
    """
    if correct_title:
        title_correction(rec)

    fastinfo = 'T' + rec.title
    subtitles = getattr(rec, 'subtitles', None)
    if subtitles:
        fastinfo += '\nt' + simplejson.dumps(subtitles)
    title_ignore_chars = getattr(rec, 'title_ignore_chars', None)
    if title_ignore_chars:
        fastinfo += '\n#%s' % title_ignore_chars
    title_indexparts = getattr(rec, 'title_indexparts', None)
    if title_indexparts:
        fastinfo += '\ni%s' + title_indexparts
    author = getattr(rec, 'author', None)
    if author:
        fastinfo += '\nA' + author
    origin = getattr(rec, 'origin', None)
    if origin:
        fastinfo += '\nO' + origin
    pubplace = getattr(rec, 'pubplace', None)
    if pubplace:
        fastinfo += '\nL' + pubplace
    publisher = getattr(rec, 'publisher', None)
    if publisher:
        fastinfo += '\nP' + publisher
    pubyear = getattr(rec, 'pubyear', None)
    if pubyear:
        fastinfo += '\nY%s' % pubyear
    isbn = getattr(rec, 'isbn', None)
    if isbn:
        fastinfo += '\nI%s' % isbn
    keys = getattr(rec, 'keys', None)
    if keys:
        if type(keys) in (tuple, list):
            keys = REPEATJOINER.join(keys)
        fastinfo += '\nK' + keys
    return fastinfo


def split_crazy_tail(txt):  # , convert_tail=True
    """
        some libraries add into data connecting strings to next data (yes, it's really crazy)
        we split here (as exact as possible) the real data and the crazy connector (=crazy_tail)
        because we split the crazy_tail in order to save it somewhere,
            ### removed: ### it will be converted into an internal format; you can disable this by setting convert_tail=False

        Returns: (real data, crazy_tail)  # both strings
    """
    tail = txt[-5:]
    crazy_tail = re.findall(r'[ +\-/:,;]+$', tail)
    if crazy_tail:
        crazy_tail = crazy_tail[0]
        if crazy_tail.strip():
            txt = txt[:(len(txt) - len(crazy_tail))]
            if crazy_tail[0] == ' ' and crazy_tail[-1] != ' ':
                crazy_tail += ' '
            #if convert_tail:
            #    crazy_tail = '$%s$%s$' % (len(crazy_tail), crazy_tail)
            return txt, crazy_tail
    rstr = txt.rstrip()
    if rstr[-1:] == '.' and rstr[-2:] != '..':
        return rstr[:-1], txt[len(rstr) - 1:]
    return rstr, ' : '  # TODO? at this time we use ' : ' as default crazy_tail connector, but this behaviour
                        #   should be improved (or connector changed later) based on the (marc) type of the next subtitle


def parse_fbi(question, libstyle, reverted=True):
    """can asked string be a rik(fbi)?
    return:
        None,None if cannot
        rik,None|iorder (rik(fbi) of book, iorder(order of impression for given book) if present)
    note: always the same rik_width must be used in the library,
            so non-digit separator between rik and iorder is possible but not neccessary
        if for the growing library shorter rik(fbi) will be allowed in the future (using additional parameter allow_shorter=True),
            then non-digit separator would stay obligatory
    """
    rik_width = libstyle['lrik']
    rik = question[:rik_width]
    if len(rik) < rik_width or not rik.isdigit() or not question[-1].isdigit():
        return None, None
    iorder = None
    tail = re.findall('\d+$', question[rik_width:])
    if tail:
        tail = int(tail[0])
        if tail > 0:
            iorder = tail
    if reverted:
        return rik[::-1], iorder
    else:
        return rik, iorder


def ean_to_fbi(ean):
    """convert last numbers of EAN into (reverted) rik(fbi) or creates a random one
    rik(fbi) is designed to find books easier without barcode readers
    """
    return ean[:-7:-1] if (ean and len(ean) >= 6) else None
    # 7,6,6 pro len(rik)==6


def suplemental_fbi():
    """
        rik(fbi) is designed to find books easier without barcode readers
    """
    return ''.join(random.choice(string.digits) for _ in range(6))


def limit_rows(rows, limitby):
    """will shorten an iterable to limitby items
        limitby can be integer or tuple/list length=2 (lower and upper boundary)
    return tuple : (shortened iterable, was_longer?)
    this is suitable for SQL queries made with LIMIT BY limitby+1 to obtain info if we have more records as was just fetched
    """
    if isinstance(limitby, (tuple, list)):
        limitby = limitby[1] - limitby[0]
    if len(rows) > limitby:
        return rows[:limitby], True
    else:
        return rows, False


def parse_fastinfo(fastinfo):
    """will parse fastinfo blob into tuple: (title, author, publisher, pubyear)
    """
    book_dict = defaultdict(lambda: [])
    for ln in fastinfo.splitlines():
        if len(ln) > 1:
            book_dict[ln[:1]].append(ln[1:])
    return REPEATJOINER.join(book_dict['T']), REPEATJOINER.join(book_dict['A']), REPEATJOINER.join(book_dict['P']), REPEATJOINER.join(book_dict['Y'])  # tit, aut, pub, puy


def parse_year_from_text(txt, minyear=1600, maxyear=datetime.date.today().year + 3, as_string=False):
    year = ''
    for num in re.findall('\d+', txt):
        if minyear <= int(num) <= maxyear:
            year = num
            break
    return year if as_string else (int(year) if year else None)


def get_publisher(publishers, src_joiner=';'):
    if type(publishers) not in (tuple, list):
        publishers = [publisher.strip() for publisher in publishers.split(src_joiner)]
    return REPEATJOINER.join(publishers)


def get_place_publisher(pubplace, publisher):
    if type(publisher) in (tuple, list):
        publisher = get_publisher(publisher)
    return ' : '.join((pubplace, publisher))


def make_unique(parts, safe_first=True, part_extraction=lambda p: p):
    """
        seek for parts*) if some of them could be joined from other parts; if so, such part will be removed
        this is because we have in marc sources often such kind of unnecessary duplicates in the marc title (245/246) subfields
        *) parts are
            parts[1:] if safe_first=True (never remove the first item)
            or all of them if safe_first=False

        part_extraction is for internal use (see make_unique_tuples())
    """
    stop = 0 if safe_first else None
    parts = list(parts)
    len_parts = len(parts)
    for revpos1, part in enumerate(parts[:stop:-1]):
        pos1 = len_parts - revpos1 - 1
        testpart = part_extraction(part)
        for pos2, part in enumerate(parts):
            if pos1 != pos2 and part:  # and part: some part can already be replaced, so without this part_extraction() will fail
                testpart = testpart.replace(part_extraction(part), '')
        if not re.findall('\w', unicode(testpart), flags=re.UNICODE):  # part can be joined from other parts (we ignore any connecting characters here)
            parts[pos1] = ''                # remove it (but in 2 steps to avoid item movement inside the cycle)
    return filter(None, parts)              # this is 2nd step of removing


def make_unique_tuples(parts, safe_first=True):
    """
        works like make_unique() but works with tuples where each part is in tuple[1]
    """
    return make_unique(parts, safe_first=safe_first, part_extraction=lambda p: p[1])


def title_correction(rec):
    """
        isolates
            - main title (string)
            - subtitles (list of tuples, first item is connector to the previous part(s), second is subtitle itself)
        this handles 2 types of crazy title representations:
            - 'title : subtitle' inside the title value
            - crazy_tails ie. extra characters added to the end of real title/subtitle value which should connect the next parts in the printed output
                this crazy solution (which heavy breaks the value of data) is really used in real life: at least in Czech national library databases

        TODO? maybe we will need this later with title/subtitle parameters and/or title/subtitle return value,
            but at now we make this correction inside the rec object (containing rec.title, rec.subtitles)
    """
    title_parts = rec.title.lstrip().split(' : ')
    subtitles_input = getattr(rec, 'subtitles', None)
    if subtitles_input:
        if isinstance(subtitles_input, basestring):
            subtitles_input = (subtitles_input,)
        title_parts.extend(subtitles_input)
    subtitles = []
    next_crazy = None
    for title_part in title_parts:
        title_part, crazy_tail = split_crazy_tail(title_part)
        subtitles.append((next_crazy, title_part))
        next_crazy = crazy_tail
    subtitles = make_unique_tuples(subtitles)

    rec.title = subtitles.pop(0)[1]
    rec.subtitles = subtitles
