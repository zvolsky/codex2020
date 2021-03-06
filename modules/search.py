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
        ' ',
        INPUT(_name='cat', _type='radio', _value='W', _checked=''),
        SPAN(T("slovo")),
        ' ',
        INPUT(_name='cat', _type='radio', _value='A'),
        SPAN(T("autor")),
        #' ',
        #INPUT(_name='cat', _type='radio', _value='t'),   # incl. subtitle
        #SPAN(T("titul")),
        ' ',
        INPUT(_type='submit', _value=T("najdi")),
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
        lbflds = (db.library.id, db.library.is_public, db.library.library, db.library.slug, db.library.news_cnt)
        if lbid:
            lbrow = db(db.library.id == lbid).select(*lbflds).first()
        else:
            lbrow = db(db.library.slug == lbslug).select(*lbflds).first()
        if lbrow and (lbrow.is_public or
                    auth.user_id and
                    (auth.has_membership('admin') or db((db.auth_lib.auth_user_id == auth.user_id) & (db.auth_lib.library_id == lbrow.id)).select(db.auth_lib.id))):
            library = lbrow
    return library


def handle_qb_form(vars, lbid=None, lbslug=None, db=None, response=None, T=None):
    if db is None:
        db = current.db
    if response is None:
        response = current.response
    if T is None:
        T = current.T

    library = lib_by_slug_or_id(lbid=lbid, lbslug=lbslug)  # None | row
    if library and library.news_cnt > 0:
        news_status = 0
    else:
        news_status = -1

    parsed_rows = []
    html = []
    rows = None
    flds = [db.answer.id, db.answer.fastinfo, db.answer.ean]
    db.owned_book._common_filter = None
    if vars.qb:
        qb = slugify(vars.qb)
        if vars.cat == 'W':
            query = db.idx_word.word.startswith(qb)
            wordjoin = [db.answer.on(db.answer.id == db.idx_word.answer_id)]
        elif vars.cat == 'A':
            query = db.idx_long.item.startswith(qb) & (db.idx_long.category == 'A')
            wordjoin = [db.idx_join.on(db.idx_join.idx_long_id == db.idx_long.id),
                        db.answer.on(db.answer.id == db.idx_join.answer_id)]
        '''
        elif vars.cat == 't':
        '''
        if library:
            lib_query = db.owned_book.library_id == library.id
            query = query & lib_query
            flds.append(db.owned_book.cnt)
            #wordjoin.append(db.owned_book.on(db.owned_book.answer_id == db.idx_word.answer_id)) # this was valid for 'W' only
            wordjoin.append(db.owned_book.on(db.owned_book.answer_id == db.answer.id))
        # else: # TODO? vrací navíc nějaká divná pole: ['impression', 'book_publisher', 'update_record', 'book_authority', 'owned_book', 'idx_word', 'fastinfo', 'rik2', 'idx_join', 'lib_descr', 'id', 'delete_record', 'idx_short']
        rows = db(query).select(*flds, join=wordjoin, distinct=db.answer.id)

    elif news_status >= 0:
        lib_query = db.owned_book.library_id == library.id
        flds.append(db.owned_book.id)
        rows = db(lib_query).select(*flds,
                join=db.owned_book.on(db.owned_book.answer_id == db.answer.id),
                orderby=~db.owned_book.id,
                limitby=(0, library.news_cnt)
                )
        news_status = 1 if rows else -1

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
                book_line = A(book_line, _href="https://www.obalkyknih.cz/view?isbn=%s" % book['ean'], _class="book-link",
                              _onmouseover="bookLinkOver('%s')" % book['ean'])
            html.append(book_line)

    elif rows is not None:
        response.flash = T("Nenalezeno")

    return (library, DIV(*html, _class="list-group"), news_status)
