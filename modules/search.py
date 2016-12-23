# -*- coding: utf-8 -*-

from gluon import current
from gluon.tools import URL, redirect

from mzutils import slugify


def handle_qb_form(form_vars, db=None, session=None, T=None):
    if db is None:
        db = current.db
    if session is None:
        session = current.session
    if T is None:
        T = current.T

    qb = slugify(form_vars.qb)
    rows = db(db.idx_word.word.startswith(qb)).select(
        db.answer.id, db.answer.fastinfo,
        join=db.answer.on(db.answer.id == db.idx_word.answer_id),
        distinct=db.answer.id
    )
    if not rows:
        session.flash = T("Nenalezeno")
        redirect(URL('default', 'index'))
    return len(rows)
