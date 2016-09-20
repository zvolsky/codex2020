# -*- coding: utf-8 -*-

"""Codex 2020 utils, completely independent on the Web2py framework
"""

from collections import defaultdict
import datetime
import hashlib
import random
import re
import string

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


def publ_fastinfo_and_hash(title, surnamed_author, author, pubplace, publisher, pubyear, subtitle=None, keys=None):
    return (make_fastinfo(title, author, pubplace=pubplace, publisher=publisher, pubyear=pubyear, subtitle=subtitle, keys=keys),
            publ_hash(title, surnamed_author, publisher, pubyear, subtitle=subtitle))


def publ_hash(title, author, publisher, pubyear, subtitle=None, author_need_normalize=False):
    """
    author: prefered use is 'surname shortened'string. For anything else (list, not shortened,..) please set author_need_normalize
    publisher: publisher1 publisher2 ...
    pubyear: we use digits only
    """
    if subtitle:
        title = title + subtitle  # connection not important: hash_prepared() removes all
    if author_need_normalize:
        author, _full = normalize_authors(author, string_surnamed=True)

    src = '%s|%s|%s|%s' % (hash_prepared(title), hash_prepared(author),
                           hash_prepared(publisher), filter(lambda d: d.isdigit(), pubyear))
    if type(src) == unicode:
        src = src.encode('utf-8')
    return hashlib.md5(src).hexdigest()


def make_fastinfo(title, author, pubplace=None, publisher=None, pubyear=None, subtitle=None, isbn=None, keys=None):
    """
    Args:
        keys: accepts iterable (recommended) or string (use REPEATJOINER please)
    """
    title = title.split(' : ')
    fastinfo = 'T' + title.pop(0).strip()
    if subtitle:
        title.append(subtitle)
    title = filter(None, map(lambda a: a.strip(), title))
    if title:
        fastinfo += '\nt' + '. '.join(title)
    fastinfo += '\nA' + author
    if pubplace:
        fastinfo += '\nL' + pubplace
    if publisher:
        fastinfo += '\nP' + publisher
    if pubyear:
        fastinfo += '\nY%s' % pubyear
    if isbn:
        fastinfo += '\nI%s' % isbn
    if keys:
        if type(keys) in (tuple, list):
            keys = REPEATJOINER.join(keys)
        fastinfo += '\nK' + keys
    return fastinfo


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
