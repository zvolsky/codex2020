# -*- coding: utf-8 -*-

"""Codex 2020 utils, completely independent on the Web2py framework
"""

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

def parse_fbi(question, libstyle):
    """can asked string be a rik(fbi)?
    return:
        None,None if cannot
        rik,None|iorder (rik(fbi) of book, iorder(order of impression for given book) if present)
    note: always the same rik_width must be used in the library,
            so non-digit separator between rik and iorder is possible but not neccessary
        if for the growing library shorter rik(fbi) will be allowed in the future (using additional parameter allow_shorter=True),
            then non-digit separator would stay obligatory
    """
    rik_width = libstyle['id'][3]
    rik = question[:rik_width]
    if len(rik) < rik_width or not rik.isdigit() or not question[-1].isdigit():
        return None, None
    iorder = None
    tail = re.findall('\d+$', question[rik_width:])
    if tail:
        tail = int(tail[0])
        if tail > 0:
            iorder = tail
    return rik, iorder

def ean_to_fbi(ean):
    """convert last numbers of EAN into (reverted) rik(fbi) or creates a random one
    rik(fbi) is designed to find books easier without barcode readers
    """
    return ean[:-6:-1] if (ean and len(ean) >= 5) else ''.join(random.choice(string.digits) for _ in range(5))
