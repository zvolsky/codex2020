# -*- coding: utf-8 -*-

from books import can_be_isxn, isxn_to_ean

from c2_db import PublLengths, parse_fbi
from global_settings import USE_TZ_UTC


@auth.requires_login()
def review():
    """
    At his time we accept everything in impr_hist as founded book:
        We accept for now 'l!' (dun [cz:upomínka])
        We accept for now HACTIONS_TMP_LOST='r?' too, because we report them separately
    """
    from global_settings import HACTIONS_TMP_LOST

    if not auth.library_id:
        redirect(URL('default', 'index'))
    review_date = db(db.library.id == auth.library_id).select(db.library.review_date).first().review_date
    if USE_TZ_UTC:
        review_time = datetime.datetime(review_date.year, review_date.month, review_date.day)
    else:  # use library tz (must be from client settings!, default for settings can be from clients javascript)
        #review_time =
        assert False, 'Not implemented yet.'
    #tmp_lost = db((db.impression) & (db.impr_hist.haction == HACTIONS_TMP_LOST)).select(
    #                       left=db.impr_hist.on(db.impr_hist.impression_id == db.impression.id),
    #                       orderby=~db.impr_hist.htime)
    cnt_missing = db((db.impression.id > 0) & (db.impr_hist.impression_id == db.impression.id) & (db.impr_hist.htime >= review_time)).count(
                    distinct=db.impression.id)
    return dict(cnt_t=db(db.owned_book).count(), cnt_i=db(db.impression).count(),
                cnt_tmp_lost=0, cnt_missing=0, review_date=review_date)

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
        #answer.rik.startswith(rik)

        '''
        query = db.answer.ean == ean
        my_books = db((db.owned_book.id > 0) & query).select(db.answer.id, db.answer.fastinfo,
                                                             join=db.answer.on(db.answer.id == db.owned_book.answer_id))
        '''
    if len(question) <= PublLengths.barcode:
        #impression.barcode=

    # vlož 'r*' pro každý nalezený
