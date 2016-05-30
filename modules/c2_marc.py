# -*- coding: utf-8 -*-

import datetime
import hashlib
import random
import string

from pymarc import MARCReader    # pymarc from PyPI, see setup.py about problems

from gluon import current

from books import isxn_to_ean
from c2_db import PublLengths, create_idxs, del_idxs
from marc_dialects import MarcFrom_AlephCz


def parse_Marc_and_updatedb(results):
    touched = []
    inserted = 0
    for r in results:
        for record in MARCReader(r.data, to_unicode=True):  # will return 1 record
            inserted += updatedb(record, touched)
    duration_marc = datetime.datetime.utcnow()

    for answer_id, marcrec, record, fastinfo in touched:
        if fastinfo is not None:
            del_idxs(answer_id)  # delete related indexes before re-creating them
        create_idxs(answer_id, marcrec, record, fastinfo)

    return len(results), inserted, duration_marc


def updatedb(record, touched):
    db = current.db
    def exists_update():
        if row:                           # same ean or same significant data -> same book
            if row.md5marc != md5marc:    # yes, same book, but changed info
                db.answer[row.id] = answer
                touched.append((row.id, marcrec, record, row.fastinfo or ''))  # or '': to be sure to distinguish from insert
            return True  # row exists, stop next actions

    marc = record.as_marc()
    md5marc = hashlib.md5(marc).hexdigest()

    marcrec = MarcFrom_AlephCz(record)
    md5publ = hashlib.md5(('%s|%s|%s|%s' % (marcrec.title, marcrec.joined_authors(), marcrec.publisher, marcrec.pubyear)).encode('utf-8')).hexdigest()

    isbn = marcrec.isbn[:PublLengths.isbn]
    ean = isxn_to_ean(isbn)

    answer = dict(md5publ=md5publ, md5marc=md5marc, ean=ean, marc=marc,
                  country=marcrec.country[:PublLengths.country],
                  year_from=marcrec.pubyears[0], year_to=marcrec.pubyears[1])

    '''#---------
    new = dict(ean=ean, title=marcrec.title[:PublLengths.title], isbn=isbn[:PublLengths.isbn],
            uniformtitle=(record.uniformtitle() or '')[:PublLengths.uniformtitle],
            series=marcrec.series[:PublLengths.series],
            subjects='; '.join(marcrec.subjects)[:PublLengths.subjects],
            categories='; '.join(map(lambda r:r[0] + (' ('+r[1]+')' if r[1] else ''), marcrec.categories))[:PublLengths.categories],
            addedentries='; '.join(fld.value() for fld in (record.addedentries() or []))[:PublLengths.addedentries],
            publ_location='; '.join(fld.value() for fld in (record.location() or []))[:PublLengths.publ_location],
            notes='; '.join(fld.value() for fld in (record.notes() or []))[:PublLengths.notes],
            physicaldescription='; '.join(fld.value() for fld in (record.physicaldescription() or []))[:PublLengths.physicaldescription],
            publisher=marcrec.publisher[:PublLengths.publisher],
            pubyear=marcrec.pubyear[:PublLengths.pubyear],
            author=marcrec.author[:PublLengths.author],
            )
    db.publication.insert(**new)
    #---------'''

    flds = (db.answer.id, db.answer.md5marc, db.answer.fastinfo)
    if ean:
        if ean[:3] == '977':  # can have everything in [10:12] position
            row = db(db.answer.ean.startswith(ean[:10])).select(*flds).first()
        else:
            row = db(db.answer.ean == ean).select(*flds).first()
        if exists_update():   # row exists...
            return False      # ...do not continue to find (using significant data) and do not insert
    # no isbn/ean
    row = db(db.answer.md5publ == md5publ).select(*flds).first()
    if exists_update():
        return False
    else:                                    # row doesn't exist...
        answer['rik'] = ''.join(random.choice(string.digits) for _ in range(5))
        row_id = db.answer.insert(**answer)  # ...insert it
        touched.append((row_id, marcrec, record, None))
        return True  # True -> + 1 into inserted count
