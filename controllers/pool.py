# -*- coding: utf-8 -*-

from gluon.contrib import simplejson

from plugin_mz import formstyle_bootstrap3_compact_factory

from dal_common import review_imp_book
from dalc_pool import get_review_time

from c2_common import fmt_impressions_by_usrid, fmt_impression_plain
from global_settings import HACTIONS_TMP_LOST


@auth.requires_login()
def review():
    """
    At this time we accept everything in impr_hist as founded book:
        We accept for now 'l!' (dun [cz:upomínka])
        We accept for now HACTIONS_TMP_LOST='r?' too, because we report them separately
    """

    if not auth.library_id:
        redirect(URL('default', 'index'))

    review_date, review_time = get_review_time()
    return dict(cnt_t=db(db.owned_book).count(), cnt_i=db(db.impression).count(),
                cnt_tmp_lost=db(db.impression.haction == HACTIONS_TMP_LOST).count(),
                cnt_found=db(db.impression.htime >= review_time).count(), review_date=review_date)

# ajax
@auth.requires_login()
def review_find():
    """we accept: ean/isxn, own barcode, rik(fbi)
    """
    question = request.vars.q
    imp_id, candidates = fmt_impressions_by_usrid(question)  # imp_id only if we have SINGLE impression
    imp = review_imp_book(imp_id)                            # will be successful if we have SINGLE impression
    if imp:
        finished = fmt_impression_plain(imp)
        return simplejson.dumps(('F', finished.xml()))
    else:
        candidates = DIV(candidates, _class="well well-sm")
        return simplejson.dumps(('C', candidates.xml()))

# ajax
@auth.requires_login()
def review_doit():
    imp_id = request.args[0]
    imp = review_imp_book(imp_id)
    if imp:
        finished = fmt_impression_plain(imp)
    else:
        finished = T("Selhalo nalezení výtisku (kontaktuj podporu, pokud problém přetrvává).")
    return simplejson.dumps(finished.xml())

@auth.requires_login()
def missing():
    review_date, review_time = get_review_time()
    grid = SQLFORM.grid((db.impression.htime < review_time) & (db.impression.haction != HACTIONS_TMP_LOST))
    return dict(grid=grid, review_date=review_date,
                cnt_missing=db((db.impression.htime < review_time) & (db.impression.haction != HACTIONS_TMP_LOST)).count())
    #db.impression.ALL, db.answer.fastinfo, join=db.answer.on(db.answer.id == db.impression.answer_id)

@auth.requires_login()
def lost():
    grid = SQLFORM.grid(db.impression.haction == HACTIONS_TMP_LOST)
    return dict(grid=grid,
                cnt_tmp_lost=db(db.impression.haction == HACTIONS_TMP_LOST).count())
    #db.impression.ALL, db.answer.fastinfo, join=db.answer.on(db.answer.id == db.impression.answer_id)
