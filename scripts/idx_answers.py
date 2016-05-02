# -*- coding: utf-8 -*-

from pymarc import MARCReader    # pymarc from PyPI

from gluon import current
current.db = db

from c2_db import create_idxs, truncate_idxs
from c2_marc import get_idx_data
from marc_dialects import MarcFrom_AlephCz


# at this time only marc_id==1 is supported (Aleph/cz records)
def idx_answers():
    truncate_idxs()

    cnt = 0
    answer_id = -1
    while True:
        rows = db((db.answer.id > answer_id) & (db.answer.marc_id == 1)).select(
                db.answer.id, db.answer.marc, orderby=db.answer.id, limitby=(0, 500))
        if not rows:
            break
        for row in rows:
            record = MARCReader(row.marc, to_unicode=True).next()
            marcrec = MarcFrom_AlephCz(record)
            create_idxs(row.id, get_idx_data(marcrec, record))

            answer_id = row.id
            cnt += 1
        db.commit()
        print cnt


if __name__ == '__main__':
    idx_answers()
