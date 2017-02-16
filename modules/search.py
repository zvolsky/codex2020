# -*- coding: utf-8 -*-

from gluon import current
from gluon.tools import URL, redirect
from gluon.html import DIV, SPAN, INPUT, FORM
from gluon.validators import IS_NOT_EMPTY

from c_utils import parse_fastinfo
from c2_common import get_book_line

from mzutils import slugify


def get_qb_form(T=None):
    if T is None:
        T = current.T

    return FORM(
        INPUT(_name='qb', requires=IS_NOT_EMPTY()),
        INPUT(_type='submit', _value=T("najdi publikace")),
    )


def handle_qb_form(qb, db=None, session=None, T=None):
    if db is None:
        db = current.db
    if session is None:
        session = current.session
    if T is None:
        T = current.T

    qb = slugify(qb)
    rows = db(db.idx_word.word.startswith(qb)).select(
        db.answer.id, db.answer.fastinfo, db.answer.ean,
        join=db.answer.on(db.answer.id == db.idx_word.answer_id),
        distinct=db.answer.id
    )    # TODO? vrací navíc nějaká divná pole: ['impression', 'book_publisher', 'update_record', 'book_authority', 'owned_book', 'idx_word', 'fastinfo', 'rik2', 'idx_join', 'lib_descr', 'id', 'delete_record', 'idx_short']
    if not rows:
        session.flash = T("Nenalezeno")
        redirect(URL('default', 'index'))
    parsed_rows = []
    for row in rows:
        tit, aut, pub, puy = parse_fastinfo(row.fastinfo)
        parsed_rows.append(dict(tit=tit, aut=aut, pub=pub, puy=puy, ean=row.ean))
    books = sorted(parsed_rows, key=lambda row: row['puy'], reverse=True)

    # render
    html = []
    for book in books:
        book_line = get_book_line(book['tit'], book['aut'], book['pub'], book['puy'])
        book_line = SPAN(book_line, _class="list-group-item")
        if book('ean'):
            book_line = A(book_line, _href="https://www.obalkyknih.cz/view?isbn=%s" % book('ean'), _class="book-row")
        html.append(book_line)

    return dict(books=DIV(*html, _class="list-group"))
