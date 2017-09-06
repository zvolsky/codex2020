# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

from books import can_be_isxn, isxn_to_ean

from gluon import current

from c_common import group_imp_by_book
from c_db import PublLengths
from c_utils import parse_fbi
from dal_utils import get_libstyle


def hide_all_fields(tbl):
    for sfld in tbl.fields:
        fld = tbl[sfld]
        fld.writable = fld.readable = False


def get_my_libraries_with_names(db=None):
    if db is None:
        db = current.db

    return db(db.auth_lib).select(db.library.id, db.library.library, db.auth_lib.rw,
                                  join=db.library.on(db.auth_lib.library_id == db.library.id))


def get_all_libraries(admin=False, exclude_ids=False, db=None):
    if db is None:
        db = current.db

    if admin:
        query = db.library
    else:
        query = db.library.ltype != 'tst'   # exclude testing
    libraries = db(query).select(db.library.id, db.library.library)

    if exclude_ids:
        libraries = libraries.find(lambda row: row.id not in exclude_ids)

    return libraries


def get_all_libraries_with_names(db=None):
    if db is None:
        db = current.db

    return db(db.auth_lib).select(
            db.auth_lib.library_id, db.library.library, db.library.read_pwd,
            ignore_common_filters=True)


def get_imp_book(imp_id, db=None):
    """based on impression.id (imp_id)
    this will retrieve None or single row: imp.impression(id,iorder,iid,sgn)+imp.answer(rik,fastinfo)
    """
    if db is None:
        db = current.db

    return db(db.impression.id == imp_id).select(
            db.impression.id, db.impression.iorder, db.impression.iid, db.impression.sgn,
            db.answer.rik, db.answer.fastinfo,
            left=db.answer.on(db.answer.id == db.impression.answer_id)
            ).first()


def impressions_by_usrid(question, stop_if_single=False, db=None):
    """this is search for review, for loans, ...
    barcode, isXn, ean, rik/fbi or (?TODO: begin of title) are accepted as question
    Args:
        stop_if_single: if we are in case of SINGLE resulting impression insterested in its id ONLY, we can minimal speed up the call with setting to True
    Rrturns: tuple (books, overflow, imp_id)
        books: list of grouped impressions
        overflow: True if there were more rows as in limitby setting (see bellow)
        imp_id: id of the impression if exactly SINGLE is found
    """
    if db is None:
        db = current.db

    def nothing():
        return ([], False, None)

    if not len(question):
        return nothing()

    limitby = 50

    libstyle = get_libstyle()
    query = False
    if libstyle['bc'][0] == 'B' and len(question) <= PublLengths.barcode:  # TODO: formal control for valid barcode syntax would be good, but must be library dependent
        query = db.impression.barcode == question

    if libstyle['id'][0] == 'I' and len(question) <= PublLengths.iid:
        query |= db.impression.iid == question

    if can_be_isxn(question):
        ean = isxn_to_ean(question)
        query |= db.answer.ean == ean
    rik, iorder = parse_fbi(question, libstyle)
    if rik:
        rik_query = db.answer.rik.startswith(rik)
        if iorder:
            query |= (db.impression.iorder == iorder) & rik_query
        else:
            query |= rik_query

        rik2ids = [row.answer_id for row in db(db.rik2.rik2.startswith(rik)).select(db.rik2.answer_id)]
        if rik2ids:  # it can be a suplemental rik replaced later by real rik (given by ean)
            query |= db.answer.id.belongs(rik2ids)

    if not query:
        return nothing()

    imp_order = db.impression.iid if libstyle['id'][0] == 'I' else db.impression.iorder
    imps = db(query).select(db.impression.id, db.impression.iorder, db.impression.iid, db.impression.sgn,
                            db.owned_book.id, db.answer.id, db.answer.rik, db.answer.fastinfo,
                            join=(db.owned_book.on(db.owned_book.id == db.impression.owned_book_id),
                                db.answer.on(db.answer.id == db.impression.answer_id)),
                            orderby=(db.owned_book.id, imp_order))

    if len(imps) == 1:
        imp_id = imps[0].impression.id
        if stop_if_single:
            return None, None, imp_id
    else:
        imp_id = None

    books, overflow = group_imp_by_book(imps, limitby=limitby)
    return books, overflow, imp_id
