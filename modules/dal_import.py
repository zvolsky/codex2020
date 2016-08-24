# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

from gluon import current


def load_redirects(db=None):
    if db is None:
        db = current.db

    redirects = db().select(db.import_redirect.md5publ, db.import_redirect.answer_id)
    return {redir.md5publ: redir.answer_id for redir in redirects}
