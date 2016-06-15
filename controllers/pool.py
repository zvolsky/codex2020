# -*- coding: utf-8 -*-

from global_settings import USE_TZ_UTC


@auth.requires_login()
def review():
    """
    We accept for now 'l!' (dun)
    We accept for now HACTIONS_TMP_LOST='r?' too, because we report them separately
    HACTIONS_TMP_LOST = 'r?'  # ignore in pool revision   # we accept l! for now
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
