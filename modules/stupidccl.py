# -*- coding: utf-8 -*-

"""stupidccl

provides possibility create a CCL query for Z39.50 protocol

use the CCLConfig() instance in method calls to give them info about required target CCL elements

'catalogue' method create an automatic query: for large numbers ISBN, otherwise Title (+ Author if comma inside)
"""

import re

class CCLConfig(object):
    def __init__(self, word_connect=' !0 ', title='WTL', author='WAU', isbn='ISN', **more):
        """title, autor, isbn are required for catalogue method"""
        self.word_connect = word_connect
        self.title = title
        self.author = author
        self.isbn = isbn
        for key in more:
            setattr(self, key, more[key])

def catalogue(txt, ccl_config=CCLConfig()):
    """creates CCL query suitable for catalogize
    will autodetect txt as EAN/ISBN/text and create a CCL query to get candidates records to catalogue such book
    for large numbers creates ISBN query, otherwise Title (+ Author if comma inside) query
    examples:
        .catalogue('9783886181926') -> 'ISN=9783886181926 or ISN=3886181928'
        .catalogue('Řecko a ostrovy') -> 'WTL="\xc5\x98ecko !0 a !0 ostrovy"'
        .catalogue('Hašek, Jaroslav') -> 'WTL="Ha\xc5\xa1ek, !0 Jaroslav" or WAU="Ha\xc5\xa1ek, !0 Jaroslav"'
    """
    txt = txt.strip()
    if len(txt) >= 8 and txt.replace('-', '').isdigit():  # ISBN
        parts = [(ccl_config.isbn, txt)]
        if '-' not in txt and len(txt) == 13 and txt[:3] == '978':  # can have old ISBN (10-char)
            parts.append((ccl_config.isbn, ean2isbn(txt)))
    else:
        txt = re.sub('\s+', ccl_config.word_connect, txt)
        parts = [(ccl_config.title, txt)]
        if ',' in txt:
            parts.append((ccl_config.author, txt))
    return parts2ccl(parts)

def parts2ccl(parts, connect='or'):
    return (' ' + connect + ' ').join(key + "=" + val for key, val in parts)

def ean2isbn(ean):
    """convert EAN to old version (10-char) ISBN
    before the call test if EAN is 978... EAN
    old version of EAN can but not must really exist (because book can have 13-char ISBN)
    """
    significant = ean[3:-1]
    return significant + _check_digit10(significant)

def _check_digit10(firstninedigits):
    """Check sum ISBN-10."""
    val = sum((i + 2) * int(x)
              for i, x in enumerate(reversed(firstninedigits)))
    remainder = int(val % 11)
    if remainder == 0:
        tenthdigit = 0
    else:
        tenthdigit = 11 - remainder
    if tenthdigit == 10:
        tenthdigit = 'X'
    return str(tenthdigit)
