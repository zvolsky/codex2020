# -*- coding: utf-8 -*-

"""stupidquery

provides possibility create a PQL query for Z39.50 protocol

use the PQLConfig() instance in method calls to give them info about required target PQL elements

'smart' method create an automatic PQF query suitable for creating catalog: for large numbers ISBN, otherwise Title (+ Author if comma inside)
"""

import re

class PQFConfig(object):
    def __init__(self, title=4, author=1003, isbn=7, issn=8):
        """title, autor, isbn (issn) are required for 'smart' method
        defaults from http://jib-info.cuni.cz/dokumenty/techdoc/ProfilJIB.pdf
        """
        self.title = title
        self.author = author
        self.isbn = isbn
        self.issn = issn

# PQF queries: http://www.indexdata.com/yaz/doc/tools.html#pqf-examples
# PQF example: '@or @attr 1=4 @attr 3=1 "Ohře" @attr 1=4 @attr 3=1 "Berounka"'
def smart(txt, config=PQFConfig()):
    """creates PQF query suitable for catalogize
    will autodetect txt as EAN/ISBN/text and return data for query to get candidates records to catalogue such book
    for large numbers creates ISBN query, otherwise Title (+ Author if comma inside) query
    examples:
        .smart('9783886181926') -> '@or @attr 1=7 @attr 3=1 9783886181926 @attr 1=7 @attr 3=1 3886181928'
        .smart('Řecko a ostrovy') -> '@attr 1=4 @attr 3=1 "\xc5\x98ecko a ostrovy"'
        .smart('Hašek, Jaroslav') -> '@or @attr 1=4 @attr 3=1 "Ha\xc5\xa1ek, Jaroslav" @attr 1=1003 @attr 3=1 "Ha\xc5\xa1ek, Jaroslav"'
    """
    txt = txt.strip()
    nodashes = txt.replace('-', '').replace(' ','')
    if len(nodashes) >= 8 and (nodashes.isdigit() or nodashes[:1] == 'M' and nodashes[1:].isdigit()):
        # ISBN / ISSN / ISMN
        if len(txt) > len(nodashes):  # i.e. '-' or ' ' in txt:  <=> manual writing
            pqf = '@attr 1=%s @attr 3=1 %s' % (config.isbn if len(nodashes) > 9 else config.issn, nodashes)
        elif len(txt) >= 13 and txt[:3] == '977':  # ISSN
            pqf = '@attr 1=%s @attr 3=1 %s' % (config.issn, ean2issn(nodashes))
            pqf = '@or ' + pqf + (' @attr 1=%s @attr 3=1 %s' % (config.issn, nodashes[:13]))  # no idea if 977.. can be in ISSN index, but lets try it
        else:
            pqf = '@attr 1=%s @attr 3=1 %s' % (config.isbn, nodashes)
            if len(txt) == 13 and txt[:3] == '978':  # can have old ISBN (10-char)
                pqf = '@or ' + pqf + (' @attr 1=%s @attr 3=1 %s' % (config.isbn, ean2isbn10(nodashes)))
    else:
        txt = re.sub('\s+', ' ', txt)
        pqf = '@attr 1=%s @attr 3=1 "%s"' % (config.title, txt)
        if ',' in txt:
            pqf = '@or ' + pqf + (' @attr 1=%s @attr 3=1 %s' % (config.author, txt))
    return pqf

def ean2isbn10(ean):
    """convert EAN to old version (10-char) ISBN
    before the call test if EAN is 978... EAN (no need to call with 979..)
    old version of EAN can but not must really exist (because book can have 13-char ISBN)
    """
    significant = ean[3:-1]
    return significant + _check_digit10(significant)

def ean2issn(ean):
    """convert EAN to ISSN
    before the call test if EAN is 977... EAN
    """
    significant = ean[3:10]
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
