# -*- coding: utf-8 -*-

"""TODO: this should be rafactor: moved into dal_common, dal_utils, dalc_pool, ..
"""

import datetime

from mzutils import slugify

from c_utils import make_fastinfo
from gluon import current


class PublLengths(object):
    title = 255
    uniformtitle = 255
    author = 200
    isbn = 20
    series = 100
    subjects = 255
    categories = 100
    addedentries = 255
    publ_location = 255
    notes = 255
    physicaldescription = 255
    publisher = 255
    pubyear = 100
    country = 3
    rik = 6

    # for impressions
    iid = 14
    sgn = 16
    barcode = 18

    # for indexes (index tables idx..)
    iword = 16
    ishort = 3
    ilong = 60
    irole = 3

    question_min = 3
    question = 60


def answer_by_ean(db, ean, flds):
    """return: row or None
    """
    if ean[:3] == '977':  # can have everything in [10:12] position
        return db(db.answer.ean.startswith(ean[:10])).select(*flds).first()
    else:
        return db(db.answer.ean == ean).select(*flds).first()

def answer_by_hash(db, md5publ, flds):
    """return: row or None
    """
    return db(db.answer.md5publ == md5publ).select(*flds).first()

def finish_bill(bill_id):
    """will finish the opened bill
    """
    db = current.db
    session = current.session
    cnt_imp = db(db.impr_hist.bill_id == bill_id).count()   # warning: after removing impression as Mistake later, this count can stay higher
    db.bill[bill_id] = dict(cnt_imp=cnt_imp, imp_added=datetime.datetime.utcnow())
    if 'bill' in session:
        del session.bill
