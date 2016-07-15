# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

import datetime

from gluon import current
from dal_common import get_imp_book
from dal_utils import get_libstyle, add_impr_hist
from global_settings import USE_TZ_UTC


def review_imp_book(imp_id):
    """add revision row into impression history
    this is designed for selection from the impressions list (loud_if_fails=True)
    and for auto-revision (without offering the list) if user has identified SINGLE impression immediately
    Args: imp_id can be None if we haven't just SINGLE impression
    Returns: imp (info about reviewed impression which have to be formatted) or None, if nothing was reviewed
    """
    if imp_id:
        imp = get_imp_book(imp_id)
        if imp:
            new = add_impr_rev(imp.impression.id)
            return imp, new
    return None, False

def get_review_time():
    """provides tuple:
        - starting review date from library settings
        - appropriate starting review time for compare expressions where datetime.datetime is used
    """
    libstyle = get_libstyle()
    review_date = libstyle['rev']
    if USE_TZ_UTC:
        review_time = datetime.datetime.combine(review_date, datetime.datetime.min.time()) - datetime.timedelta(hours=12)
                # -12h as long as we will use UTC but without timezones setting for libraries
    else:  # use library tz (must be from client settings!, default for settings can be from clients javascript)
        #review_time =
        assert False, 'Not implemented yet.'
    return review_date, review_time

def add_impr_rev(imp_id, db=None):
    """write revision into history
    Returns: True if this should decrement the 'not-found' count
    """
    if db is None:
        db = current.db

    _dummy_review_date, review_time = get_review_time()
    new = db.impression[imp_id].htime < review_time
    add_impr_hist(imp_id, 'r*')
    return new
