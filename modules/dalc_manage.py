# -*- coding: utf-8 -*-

import datetime

from gluon import current


def finish_bill(bill_id, db=None, session=None):
    """will finish the opened bill
    """
    if db is None:
        db = current.db
    if session is None:
        session = current.session

    cnt_imp = db(db.impr_hist.bill_id == bill_id).count()   # warning: after removing impression as Mistake later, this count can stay higher
    db.bill[bill_id] = dict(cnt_imp=cnt_imp, imp_added=datetime.datetime.utcnow())
    if 'bill' in session:
        del session.bill
