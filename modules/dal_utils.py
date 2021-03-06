# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

import datetime

from gluon import current

if False:  # for IDE only, need web2py/__init__.py
    from web2py.gluon import current


def answer_by_ean(db, ean, flds):
    """return: row or None
    """
    if ean[:3] == '977':  # can have everything in [10:12] position
        return db(db.answer.ean.startswith(ean[:10])).select(*flds).first()
    else:
        return db(db.answer.ean == ean).select(*flds).first()


def answer_by_hash(db, md5publ, flds, md5redirects=None):
    """
        md5redirects: set this earlier if you want speed up the functionality in cycle calls
        return: row or None
    """
    if md5redirects is not None:
        md5publ = md5redirects.get(md5publ, md5publ)
    return db(db.answer.md5publ == md5publ).select(*flds).first()


def add_impr_hist(imp_id, haction, reader_id=None, bill_id=None, db=None):
    """add impression history in a consistent way (into impr_hist and into impression together)
    """
    if db is None:
        db = current.db

    htime = datetime.datetime.utcnow()
    db.impr_hist.insert(impression_id=imp_id, reader_id=reader_id, bill_id=bill_id, haction=haction, htime=htime)
    db.impression[imp_id] = dict(haction=haction, htime=htime)


def get_library(db=None, auth=None):
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth
    return db(db.library.id == auth.library_id).select().first()


def get_libstyle(db=None, session=None, auth=None):
    """provides information about allowed/disabled fields
    from session.libstyle if present
    and direct from db if session.libstyle is missing yet
    """
    if session is None:
        session = current.session

    if session.libstyle:
        return session.libstyle

    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth

    library = get_library(db, auth)

    libstyle = {}
    libstyle['id'] = (('I' if library.st_imp_id else ' ') +
                    str(library.st_imp_idx)[-1:] +
                    ('O' if library.st_imp_ord else ' '))
    libstyle['lrik'] = library.st_imp_rik if 2 <= library.st_imp_rik <= 5 else 3
    libstyle['bc'] = ('B' if library.st_imp_bc else ' ') + ('+' if library.st_imp_bc else '-')
    libstyle['sg'] = (('G' if library.st_imp_sg else ' ') +
                    (library.st_imp_sgmod1 or ' ') +
                    (library.st_imp_sgmod2 or ' '))
    libstyle['sgsep'] = library.st_imp_sgsep
    libstyle['gr'] = (('P' if library.st_imp_pl else ' ') +
                    ('s' if library.st_imp_st else ' ') +
                    ('S' if library.st_tit_st else ' '))
    libstyle['rev'] = library.review_date

    # session.libstyle = {'id':'I.O.', 'bc':'B+', 'sg':'G..', 'sgsep':'???', 'gr':'PsS'}  # character position IS important
    session.libstyle = libstyle
    return libstyle
