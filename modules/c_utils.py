# -*- coding: utf-8 -*-

"""Codex 2020 utils, completely independent on the Web2py framework
"""

from collections import defaultdict
import hashlib
import random
import re
import string


def publ_hash(title, author, publisher, pubyear):
    src = '%s|%s|%s|%s' % (title, author, publisher, pubyear)
    if type(src) == unicode:
        src = src.encode('utf-8')
    return hashlib.md5(src).hexdigest()

def make_fastinfo(title, author, publisher, pubyear):
    return 'T' + title + '\nA' + author + '\nP' + publisher + '\nY' + pubyear

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
    return ean[:-6:-1] if (ean and len(ean) >= 5) else ''.join(random.choice(string.digits) for _ in range(5))

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
    return '; '.join(book_dict['T']), '; '.join(book_dict['A']), '; '.join(book_dict['P']), '; '.join(book_dict['Y'])  # tit, aut, pub, puy
