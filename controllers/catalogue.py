# -*- coding: utf-8 -*-

from pymarc import MARCReader    # pymarc z PyPI
from PyZ3950 import zoom  # z https://github.com/alexsdutton/PyZ3950, pak: python setup.py install
                          # napoprvé import z Py pod rootovskými právy (něco si ještě vytvoří)
    # viz forked.yannick.io:
        # originální asl2/ chyba instalace,
        # naposled aktualizovaný Brown-University-Library/ chyba Unicode znaků

from stupidquery import smartquery, isxn_to_ean

def publikace():
    link('js/codex2020/katalogizace/publikace')
    form = SQLFORM.factory(
            Field('appendkey', 'string', length=20, label=T("Zkus najít podle"),
                comment=T("počáteční 2-3 slova názvu nebo sejmi EAN čarový kód pro vyhledání publikace")))
    return dict(form=form)

# ajax
def hledej_appendkey():
    hledat = request.vars.appendkey
    #                                       hledat=unicode(hledat,'utf-8').encode('cp1250')
    if hledat and len(hledat) >= 3:
        try:
            conn = zoom.Connection ('aleph.nkp.cz', 9991)
            res = None
        except ConnectionError:
            res = P(T("Nelze navázat spojení se souhrnným katalogem. Jste připojeni k internetu?"))
        if res is None:
            conn.databaseName = 'SKC-UTF'  # AUT-UTF # http://aleph.nkp.cz/F/?func=file&file_name=base-list
            conn.preferredRecordSyntax = 'USMARC' # UNIMARC, XML   # http://aleph.nkp.cz/web/Z39_NK_cze.htm
            conn.charset = 'UTF-8'
            query = zoom.Query('PQF', smartquery(hledat))
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
                results = None
            if results is None:
                res = P(T("Spojení se souhrnným katalogem bylo navázáno, ale dotaz selhal"))
            else:
                marc = ''
                for r in results:
                    marc += r.data
                reader = MARCReader(marc, to_unicode=True)
                res = []
                for record in reader:
                    updatedb(record)
                    res.append(LI(record.title()))
                #results[i].data
                res = UL(res)
                print 555
            conn.close()
    else:
        res = P(T("Zadej alespoň 3 znaky pro vyhledání."))
    return res

# internal - presun jinam
def updatedb(record):
    import hashlib
    title = record.title()
    author = record.author()
    publisher = record.publisher()
    pubyear = record.pubyear()
    isbn = record.isbn()
    ean = isxn_to_ean(isbn)
    md5 = hashlib.md5('|'.join([title, author, publisher, pubyear]))
    row = None
    if ean:
        if ean[:3] == '977':  # can have everything in [10:12] position
            row = db(db.publication.ean.startswith(ean[:10])).select(
                    db.publication.id, limitby=(0,1), orderby_on_limitby=False).first()
        else:
            row = db(db.publication.ean == ean).select(
                    db.publication.id, limitby=(0,1), orderby_on_limitby=False).first()
    if not row:
        row = db(db.publication.md5 == md5).select(
                db.publication.id, limitby=(0,1), orderby_on_limitby=False).first()
    new = dict(md5=md5, ean=ean, title=title, uniformtitle=record.uniformtitle(),
               author=author, isbn=isbn, subjects=record.subjects(), addedentries=record.addedentries(),
               publ_location=record.location(), notes=record.notes(), physicaldescription=record.physicaldescription(),
               publisher=publisher, pubyear=pubyear, marc=record.as_marc())
    if row:
        db[row.id] = new
    else:
        db.publication.insert(**new)