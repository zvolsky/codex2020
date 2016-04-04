# -*- coding: utf-8 -*-

import re

from PyZ3950 import zoom  # z https://github.com/alexsdutton/PyZ3950, pak: python setup.py install
                          # napoprvé import z Py pod rootovskými právy (něco si ještě vytvoří)
    # viz forked.yannick.io:
        # originální asl2/ chyba instalace,
        # naposled aktualizovaný Brown-University-Library/ chyba Unicode znaků

from books import ean2isbn10, ean2issn


def world_get(fnd):
    results = None
    try:
        conn = zoom.Connection ('aleph.nkp.cz', 9991)
        warning = None
    except ConnectionError:
        warning = T("Nelze navázat spojení se souhrnným katalogem. Jste připojeni k internetu?")
    if warning is None:
        conn.databaseName = 'SKC-UTF'  # AUT-UTF # http://aleph.nkp.cz/F/?func=file&file_name=base-list
        conn.preferredRecordSyntax = 'USMARC' # UNIMARC, XML   # http://aleph.nkp.cz/web/Z39_NK_cze.htm
        conn.charset = 'UTF-8'
        query = zoom.Query('PQF', smartquery(fnd))
        '''
            "CCL", ISO 8777, (http://www.indexdata.dk/yaz/doc/tools.tkl#CCL)
            "S-CCL", the same, but interpreted on the server side
            "CQL", the Common Query Language, (http://www.loc.gov/z3950/agency/zing/cql/)
            "S-CQL", the same, but interpreted on the server side
            "PQF", Index Data's Prefix Query Format, (http://www.indexdata.dk/yaz/doc/tools.tkl#PQF)
            "C2", Cheshire II query syntax, (http://cheshire.berkeley.edu/cheshire2.html#zfind)
            "ZSQL", Z-SQL, see (http://archive.dstc.edu.au/DDU/projects/Z3950/Z+SQL/)
            "CQL-TREE", a general-purpose escape allowing any object with a toRPN method to be used,
        '''
        try:
            results = conn.search(query)
        except Exception:
            warning = T("Spojení se souhrnným katalogem bylo navázáno, ale dotaz selhal.")
    return warning, results

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
    nodashes = txt.replace('-', '').replace(' ', '')
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
