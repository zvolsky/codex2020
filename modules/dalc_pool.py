# -*- coding: utf-8 -*-

"""Dependent on pydal, but independent on the (rest of) Web2py framework.
The exception is use of current., which makes possible calls from Web2py framework without additional parameters;
    implicit parameter set via current. is always handled at the beginning of the func
"""

import datetime

from books import can_be_isxn, isxn_to_ean

from c_utils import parse_fbi
from dal_utils import get_libstyle
from c2_db_tmp import PublLengths
from global_settings import USE_TZ_UTC


from gluon import current


def get_review_time(db=None, auth=None):
    """provides tuple:
        - starting review date from library settings
        - appropriate starting review time for compare expressions where datetime.datetime is used
    """
    if db is None:
        db = current.db
    if auth is None:
        auth = current.auth

    review_date = db(db.library.id == auth.library_id).select(db.library.review_date).first().review_date
    if USE_TZ_UTC:
        review_time = datetime.datetime.combine(review_date, datetime.datetime.min.time()) - datetime.timedelta(hours=12)
                # -12h as long as we will use UTC but without timezones setting for libraries
    else:  # use library tz (must be from client settings!, default for settings can be from clients javascript)
        #review_time =
        assert False, 'Not implemented yet.'
    return review_date, review_time
