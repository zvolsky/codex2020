# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

from books import can_be_isxn, isxn_to_ean

from c_common import group_imp_by_book
from c_utils import parse_fbi, limit_rows
from dal_utils import get_libstyle

from gluon import current


def impressions_by_usrid(question, db=None):
    """this is search for review, for loans, ...
    barcode, isXn, ean, rik/fbi or (?TODO: begin of title) are accepted as question
    """
    if db is None:
        db = current.db

    if not len(question):
        return ()

    libstyle = get_libstyle()
    need_more = True
    if len(question) <= PublLengths.barcode:  # TODO: formal control for valid barcode syntax would be good, but must be library dependent
        need_more = False
        query = db.impression.barcode == question
    else:
        query = db.impression

    if can_be_isxn(question):
        need_more = False
        ean = isxn_to_ean(question)
        query &= db.answer.ean == ean
    rik, iorder = parse_fbi(question, libstyle)
    if rik:
        need_more = False
        if iorder:
            query &= db.impression.iorder == iorder
        query &= db.answer.rik.startswith(rik)

    if need_more:
        return ()

    imp_order = db.impression.iid if libstyle['id'][0] == 'I' else db.impression.iorder
    limitby = 50
    imps = db(query).select(db.impression.id, db.impression.iorder, db.impression.iid, db.owned_book.id, db.answer.id, db.answer.rik, db.answer.fastinfo,
                           join=(db.owned_book.on(db.owned_book.id == db.impression.owned_book_id),
                                db.answer.on(db.answer.id == db.impression.answer_id)),
                           orderby=(db.owned_book.id, imp_order),
                           limitby=(0, limitby + 1))
    imps, overflow = limit_rows(imps, limitby)
    return group_imp_by_book(imps), overflow
