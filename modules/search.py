# -*- coding: utf-8 -*-

from gluon import current
from gluon.tools import URL, redirect
from gluon.html import A, DIV, SPAN, INPUT, FORM

from c_utils import parse_fastinfo
from c2_common import get_book_line

from mzutils import slugify


def get_qb_form(lbslug=None, T=None):
    if T is None:
        T = current.T

    return FORM(
        INPUT(_name='qb'),
        INPUT(_type='submit', _value=T("najdi publikace")),
        _action=URL(args=lbslug if lbslug else ())
    )


def lib_by_slug_or_id(lbid=None, lbslug=None, db=None, auth=None):
    """
        return library if user has read access to it
    Args:
        lbid:   find by library_id (this has precedence) 
        lbslug: find by slug
    Returns:
        None or library (.id, .library, .slug) if user has read access to it
    """
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth

    library = None
    if lbslug or lbid:
        lbflds = (db.library.id, db.library.is_public, db.library.library, db.library.slug)
        if lbid:
            lbrow = db(db.library.id == lbid).select(*lbflds).first()
        else:
            lbrow = db(db.library.slug == lbslug).select(*lbflds).first()
        if lbrow and (lbrow.is_public or
                    auth.user_id and
                    (auth.has_membership('admin') or db((db.auth_lib.auth_user_id == auth.user_id) & (db.auth_lib.library_id == lbrow.id)).select(db.auth_lib.id))):
            library = (lbrow.id, lbrow.library, lbrow.slug)
    return library


def handle_qb_form(qb, lbid=None, lbslug=None, db=None, response=None, T=None):
    if db is None:
        db = current.db
    if response is None:
        response = current.response
    if T is None:
        T = current.T

    library = lib_by_slug_or_id(lbid=lbid, lbslug=lbslug)  # None | (.id, .library, .slug)

    parsed_rows = []
    html = []
    if qb:
        qb = slugify(qb)
        query = db.idx_word.word.startswith(qb)
        db.owned_book._common_filter = None
        wordjoin = db.answer.on(db.answer.id == db.idx_word.answer_id)
        flds = [db.answer.id, db.answer.fastinfo, db.answer.ean]
        if library:
            query = query & (db.owned_book.library_id == library[0])
            flds.append(db.owned_book.cnt)
            rows = db(query).select(*flds,
                join=(wordjoin, db.owned_book.on(db.owned_book.answer_id == db.idx_word.answer_id)),
                distinct=db.answer.id
            )
        else:
            rows = db(query).select(*flds,
                join=wordjoin,
                distinct=db.answer.id
            )    # TODO? vrací navíc nějaká divná pole: ['impression', 'book_publisher', 'update_record', 'book_authority', 'owned_book', 'idx_word', 'fastinfo', 'rik2', 'idx_join', 'lib_descr', 'id', 'delete_record', 'idx_short']

        if rows:
            rows.compact = False  # to sure have: row.answer
            for row in rows:
                tit, aut, pub, puy = parse_fastinfo(row.answer.fastinfo)
                parsed_rows.append(dict(tit=tit, aut=aut, pub=pub, puy=puy, ean=row.answer.ean))
            books = sorted(parsed_rows, key=lambda row: row['puy'], reverse=True)

            # render
            for book in books:
                book_line = get_book_line(book['tit'], book['aut'], book['pub'], book['puy'])
                book_line = SPAN(book_line, _class="list-group-item")
                if book['ean']:
                    book_line = A(book_line, _href="https://www.obalkyknih.cz/view?isbn=%s" % book['ean'], _class="book-link", _onmouseover="bookLinkOver('%s')" % book['ean'])
                html.append(book_line)
        else:
            current.response.flash = T("Nenalezeno")

    return (library, DIV(*html, _class="list-group"))
