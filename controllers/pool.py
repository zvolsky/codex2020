# -*- coding: utf-8 -*-

from books import can_be_isxn, isxn_to_ean

from c2_db import PublLengths, parse_fbi, get_libstyle
from global_settings import USE_TZ_UTC, HACTIONS_TMP_LOST


@auth.requires_login()
def review():
    """
    At his time we accept everything in impr_hist as founded book:
        We accept for now 'l!' (dun [cz:upomínka])
        We accept for now HACTIONS_TMP_LOST='r?' too, because we report them separately
    """

    if not auth.library_id:
        redirect(URL('default', 'index'))

    review_date, review_time = __get_review_time()
    return dict(cnt_t=db(db.owned_book).count(), cnt_i=db(db.impression).count(),
                cnt_tmp_lost=db(db.impression.haction == HACTIONS_TMP_LOST).count(),
                cnt_found=db(db.impression.htime >= review_time).count(), review_date=review_date)

# ajax
@auth.requires_login()
def review_find():
    """we accept: ean/isxn, own barcode, rik(fbi)
    """
    question = request.args(0)
    if can_be_isxn(question):
        ean = isxn_to_ean(question)
        #answer.ean=
    rik, iorder = parse_fbi(question)
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

    # vlož 'r*' pro každý nalezený

@auth.requires_login()
def missing():
    review_date, review_time = __get_review_time()
    libstyle = get_libstyle()
    grid = SQLFORM.grid((db.impression.htime < review_time) & (db.impression.haction != HACTIONS_TMP_LOST))
    return dict(grid=grid, review_date=review_date,
                cnt_missing=db((db.impression.htime < review_time) & (db.impression.haction != HACTIONS_TMP_LOST)).count())
    #db.impression.ALL, db.answer.fastinfo, join=db.answer.on(db.answer.id == db.impression.answer_id)

@auth.requires_login()
def lost():
    libstyle = get_libstyle()
    grid = SQLFORM.grid(db.impression.haction == HACTIONS_TMP_LOST)
    return dict(grid=grid,
                cnt_tmp_lost=db(db.impression.haction == HACTIONS_TMP_LOST).count())
    #db.impression.ALL, db.answer.fastinfo, join=db.answer.on(db.answer.id == db.impression.answer_id)


def __get_review_time():
    review_date = db(db.library.id == auth.library_id).select(db.library.review_date).first().review_date
    if USE_TZ_UTC:
        review_time = datetime.datetime.combine(review_date, datetime.datetime.min.time()) - datetime.timedelta(hours=12)
                # -12h as long as we will use UTC but without timezones setting for libraries
    else:  # use library tz (must be from client settings!, default for settings can be from clients javascript)
        #review_time =
        assert False, 'Not implemented yet.'
    return review_date, review_time
