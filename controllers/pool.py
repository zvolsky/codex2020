# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory

from dal_utils import get_libstyle
from dalc_pool import get_review_time

from c2_common import fmt_impressions_by_usrid
from global_settings import HACTIONS_TMP_LOST


@auth.requires_login()
def review():
    """
    At his time we accept everything in impr_hist as founded book:
        We accept for now 'l!' (dun [cz:upomínka])
        We accept for now HACTIONS_TMP_LOST='r?' too, because we report them separately
    """

    if not auth.library_id:
        redirect(URL('default', 'index'))

    form = SQLFORM.factory(Field('imp_id',
                                 label=T("Zkontrolovaný výtisk"),
                                 comment=T("zadej rik, čarový kód nebo přír.číslo")),
                           formstyle=formstyle_bootstrap3_compact_factory())

    review_date, review_time = get_review_time()
    return dict(cnt_t=db(db.owned_book).count(), cnt_i=db(db.impression).count(),
                cnt_tmp_lost=db(db.impression.haction == HACTIONS_TMP_LOST).count(),
                cnt_found=db(db.impression.htime >= review_time).count(), review_date=review_date,
                form=form)

# ajax
@auth.requires_login()
def review_find():
    """we accept: ean/isxn, own barcode, rik(fbi)
    """
    question = request.args(0)
    fmt_impressions_by_usrid(question)



    ### TODO: ajax call on blur + activate .click() for review_doit() in the callback

    # return simplejson.dumps(candidates.xml())


# ajax
@auth.requires_login()
def review_doit():
    pass
    # vlož 'r*' pro každý nalezený

@auth.requires_login()
def missing():
    review_date, review_time = get_review_time()
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
