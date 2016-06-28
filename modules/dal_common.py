# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

from books import can_be_isxn, isxn_to_ean

from c_utils import parse_fbi
from dal_utils import get_libstyle

from gluon import current


def impressions_by_usrid(question, db=None):
    """this is search for review, for loans, ...
    barcode, isXn, ean, rik/fbi or (?TODO: begin of title) are accepted as question
    """
    if db is None:
        db = current.db

    use_owned = False
    if can_be_isxn(question):
        use_owned = True
        ean = isxn_to_ean(question)
        parts.append((db.owned_book.id > 0) & (db.answer.ean == ean))
    rik, iorder = parse_fbi(question, get_libstyle())
    if rik:
        pass
        #answer.rik.startswith(rik)

        '''
        query = db.answer.ean == ean
        my_books = db((db.owned_book.id > 0) & query).select(db.answer.id, db.answer.fastinfo,
                                                             join=db.answer.on(db.answer.id == db.owned_book.answer_id))
        '''
    if len(question) <= PublLengths.barcode:
        pass
        #impression.barcode=
