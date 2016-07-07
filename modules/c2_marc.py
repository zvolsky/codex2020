# -*- coding: utf-8 -*-

import datetime
import hashlib

from pymarc import MARCReader    # pymarc from PyPI, see setup.py about problems

from gluon import current

from books import isxn_to_ean
from c_utils import publ_hash, ean_to_fbi
from dal_idx import create_idxs, del_idxs
from dal_utils import answer_by_ean, answer_by_hash
from c_db import PublLengths
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
    md5publ = publ_hash(marcrec.title, marcrec.joined_authors(), marcrec.publisher, marcrec.pubyear)

    isbn = marcrec.isbn[:PublLengths.isbn]
    ean = isxn_to_ean(isbn)

    answer = dict(md5publ=md5publ, md5marc=md5marc, ean=ean, marc=marc,
                  country=marcrec.country[:PublLengths.country],
                  year_from=marcrec.pubyears[0], year_to=marcrec.pubyears[1])

    flds = (db.answer.id, db.answer.md5marc, db.answer.fastinfo)
    if ean:
        row = answer_by_ean(db, ean, flds)
        if exists_update():   # row exists...
            return False      # ...do not continue to find (using significant data) and do not insert
    # not found by isbn/ean
    row = answer_by_hash(db, md5publ, flds)
    if exists_update():
        return False
    else:                                    # row doesn't exist...
        answer['rik'] = ean_to_fbi(ean)
        row_id = db.answer.insert(**answer)  # ...insert it
        touched.append((row_id, marcrec, record, None))
        return True  # True -> + 1 into inserted count
