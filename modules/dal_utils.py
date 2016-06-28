# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

from gluon import current


def get_libstyle(db=None, session=None):
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

    library = db(db.library.id == current.auth.library_id).select().first()

    libstyle = {}
    libstyle['id'] = (('I' if library.st_imp_id else ' ') +
                    str(library.st_imp_idx)[-1:] +
                    ('O' if library.st_imp_ord else ' ') +
                    (str(library.st_imp_rik) if 2 <= library.st_imp_rik <= 5 else '3'))
    libstyle['bc'] = ('B' if library.st_imp_bc else ' ') + ('+' if library.st_imp_bc else '-')
    libstyle['sg'] = (('G' if library.st_imp_sg else ' ') +
                    (library.st_imp_sgmod1 or ' ') +
                    (library.st_imp_sgmod2 or ' '))
    libstyle['sgsep'] = library.st_imp_sgsep
    libstyle['gr'] = (('P' if library.st_imp_pl else ' ') +
                    ('s' if library.st_imp_st else ' ') +
                    ('S' if library.st_tit_st else ' '))

    # session.libstyle = {'id':'I.O.', 'bc':'B+', 'sg':'G..', 'sgsep':'???', 'gr':'PsS'}  # character position IS important
    session.libstyle = libstyle
    return libstyle