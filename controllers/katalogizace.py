# -*- coding: utf-8 -*-

from pymarc import MARCReader    # pymarc z PyPI
from PyZ3950 import zoom  # z https://github.com/Brown-University-Library/PyZ3950 nebo viz forked.yannick.io
                          #  python setup.py install

from stupidccl import catalogue

def publikace():
    link('js/codex2020/katalogizace/publikace')
    form = SQLFORM(db.publikace)
    return dict(form=form)

# ajax
def hledej_appendkey():
    hledat = request.vars.appendkey
    #                                       hledat=unicode(hledat,'utf-8').encode('cp1250')
    if hledat and len(hledat) >= 3:
        print hledat, 1
        #try:
        conn = zoom.Connection ('aleph.nkp.cz', 9991)
        res = None
        #except ConnectionError:
        #    res = P(T("Nelze navázat spojení se souhrnným katalogem. Jste připojeni k internetu?"))
        if res is None:
            conn.databaseName = 'SKC-UTF'  # AUT-UTF # http://aleph.nkp.cz/F/?func=file&file_name=base-list
            conn.preferredRecordSyntax = 'USMARC' # UNIMARC, XML   # http://aleph.nkp.cz/web/Z39_NK_cze.htm
            conn.charset = 'UTF-8'
            print hledat, 2
            query = zoom.Query('CCL', '"' + catalogue(hledat) + '"')
            print hledat, 3
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
            #try:
            #from pdb import set_trace; set_trace()
            results = conn.search(query)
            print hledat, 4
            #except Exception:
            #    results = None
            if results is None:
                res = P(T("Spojení se souhrnným katalogem bylo navázáno, ale dotaz selhal"))
            else:
                marc = ''
                for r in results:
                    marc += r.data
                reader = MARCReader(marc)
                res = []
                for record in reader:
                    res.append(LI(record.title()))
                res = UL(res)
            conn.close()
            print hledat, 5
    else:
        res = P(T("Zadej alespoň 3 znaky pro vyhledání."))
    return res
