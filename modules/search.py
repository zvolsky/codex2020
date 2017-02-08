# -*- coding: utf-8 -*-

from gluon import current
from gluon.tools import URL, redirect

from c_utils import parse_fastinfo

from mzutils import slugify


def handle_qb_form(qb, db=None, session=None, T=None):
    if db is None:
        db = current.db
    if session is None:
        session = current.session
    if T is None:
        T = current.T

    qb = slugify(qb)
    rows = db(db.idx_word.word.startswith(qb)).select(
        db.answer.id, db.answer.fastinfo,
        join=db.answer.on(db.answer.id == db.idx_word.answer_id),
        distinct=db.answer.id
    )    # TODO? vrací navíc nějaká divná pole: ['impression', 'book_publisher', 'update_record', 'book_authority', 'owned_book', 'idx_word', 'fastinfo', 'rik2', 'idx_join', 'lib_descr', 'id', 'delete_record', 'idx_short']
    if not rows:
        session.flash = T("Nenalezeno")
        redirect(URL('default', 'index'))
    parsed_rows = []
    for row in rows:
        tit, aut, pub, puy = parse_fastinfo(row.fastinfo)
        parsed_rows.append(dict(tit=tit, aut=aut, pub=pub, puy=puy))
    return dict(books=sorted(parsed_rows, key=lambda row: row['puy'], reverse=True))

