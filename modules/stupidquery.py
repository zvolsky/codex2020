# -*- coding: utf-8 -*-

"""stupidquery

provides possibility create a PQL query for Z39.50 protocol

use the PQLConfig() instance in method calls to give them info about required target PQL elements

'smartquery' method create an automatic PQF query suitable for creating catalog: for large numbers ISBN, otherwise Title (+ Author if comma inside)
"""

import re

class PQFConfig(object):
    def __init__(self, title=4, author=1003, isbn=7, issn=8):
        """title, autor, isbn (issn) are required for 'smartquery' method
        defaults from http://jib-info.cuni.cz/dokumenty/techdoc/ProfilJIB.pdf
        """
        self.title = title
        self.author = author
        self.isbn = isbn
        self.issn = issn

# PQF queries: http://www.indexdata.com/yaz/doc/tools.html#pqf-examples
# PQF example: '@or @attr 1=4 @attr 3=1 "Ohře" @attr 1=4 @attr 3=1 "Berounka"'
def smartquery(txt, config=PQFConfig()):
    """creates PQF query suitable for catalogize
    will autodetect txt as EAN/ISBN/text and return data for query to get candidates records to catalogue such book
    for large numbers creates ISBN query, otherwise Title (+ Author if comma inside) query
    examples:
        .smartquery('9783886181926') -> '@or @attr 1=7 @attr 3=1 9783886181926 @attr 1=7 @attr 3=1 3886181928'
        .smartquery('Řecko a ostrovy') -> '@attr 1=4 @attr 3=1 "\xc5\x98ecko a ostrovy"'
        .smartquery('Hašek, Jaroslav') -> '@or @attr 1=4 @attr 3=1 "Ha\xc5\xa1ek, Jaroslav" @attr 1=1003 @attr 3=1 "Ha\xc5\xa1ek, Jaroslav"'
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
    return significant + check_digit_isbn10(significant)

def ean2issn(ean):
    """convert EAN to ISSN
    before the call test if EAN is 977... EAN
    """
    significant = ean[3:10]
    return significant + check_digit_isbn10(significant)

def check_digit_isbn10(firstninedigits):
    """Check sum ISBN-10"""
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

def check_digit_ean(firsttwelvedigits):
    """Check sum EAN"""
    checksum = 0
    for pos, digit in enumerate(firsttwelvedigits[:12]):
        if pos % 2:
            checksum += int(digit) * 3
        else:
            checksum += int(digit)
    return str(10 - checksum % 10)[-1:]

def isxn_to_ean(isxn):
    """for ISSN digits [10:12] will be set to 00 - printed EAN may be different in [10:12] position"""
    isxn = isxn.strip()
    digits = ''.join(i for i in isxn if i.isdigit())
    cnt = len(digits)
    if cnt >= 12:
        return digits[:12] + check_digit_ean(digits)   # check_digit_ean will slice to [:12]
    if isxn[-1:] == 'X' and cnt == 9 or len(digits) >= 10:
        ean = '978' + digits[:9]
    elif len(digits) >= 9 and 'M' in isxn:
        ean = '9790' + digits[:8]
    elif len(digits) >= 7:
        ean = '977' + digits[:7] + '00'
    else:
        return ''
    return ean + check_digit_ean(ean)
