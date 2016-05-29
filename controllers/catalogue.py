# -*- coding: utf-8 -*-

from collections import defaultdict
import locale

from gluon.contrib import simplejson

from mzutils import slugify
from plugin_mz import formstyle_bootstrap3_compact_factory

from books import is_isxn, isxn_to_ean


COLLATING = 'cs_CZ.utf8'
EAN1 = '97880'
EAN2 = '97980'


@auth.requires_login()
def find():
    def onvalidation(form):
        if EAN1 and request.vars.question.isdigit() and len(EAN1 + request.vars.question) == 13:
            form.vars.question = EAN1 + request.vars.question
        form.vars.asked = datetime.datetime.utcnow()

    comment = T("zadej **počáteční 2-3 slova názvu** nebo sejmi **prodejní čarový kód EAN**")
    if EAN1:
        comment += ' ' + "''" + T('(z klávesnice: stiskni F8 (F9) nebo jen opiš posledních %s číslic za %s)') % (13 - len(EAN1), EAN1) + "''"
    db.question.question.comment = MARKMIN(comment)

    form = SQLFORM(db.question, hidden=dict(f8=EAN1, f9=EAN2), formstyle=formstyle_bootstrap3_compact_factory())
    if form.process(onvalidation=onvalidation).accepted:
        scheduler.queue_task(task_catalogize,
                pvars={'question_id': form.vars.id, 'question': form.vars.question, 'asked': str(form.vars.asked)},
                timeout=300)
    return dict(form=form, cancel_search=__btnCancelSearch())

# ajax
#   called via setTimeout/ajax
#   maybe this can be redesigned as a component, using LOAD() and web2py_component(url,id) function
@auth.requires_login()
def retrieve_status():
    find_status = CAT()
    questions = db((db.question.live == True) & (db.question.auth_user_id == auth.user_id)).select(
            db.question.id, db.question.question, db.question.duration_marc,
            db.question.retrieved, db.question.we_have, orderby=db.question.id)
    if questions:
        some_ready = False
        status_rows = []
        for q in questions:
            cls = 'list-group-item '
            if q.duration_marc is not None:
                cls += 'list-group-item-success active'
                some_ready = True
            status_rows.append(A(SPAN(q.retrieved or 0, _class="badge"), # první SPAN: SPAN(q.we_have or 0, _class="badge"),
                                 SPAN(q.question, _id="question"), _href='#', _class=cls, _data_id='%s' % q.id))
        if some_ready:
            hint = T("Vyber vyhledanou knihu ke katalogizaci nebo zadej další")
        else:
            hint = T("Počkej na vyhledání předchozího zadání nebo zadej další knihu ke zpracování")
        find_status = DIV(*status_rows, _class="list-group") + SPAN(hint, _class="help-block")
    return simplejson.dumps(find_status.xml())

# ajax
#   called via question click
#   maybe this can be redesigned as a component, using LOAD() and web2py_component(url,id) function
@auth.requires_login()
def retrieve_books():
    question_id = request.args(0)
    question = db(db.question.id == question_id).select(db.question.question).first().question
    if is_isxn(question):
        ean = isxn_to_ean(question)
        books = db(db.answer.ean == ean).select(db.answer.id, db.answer.fastinfo)
    else:
        books = db((db.idx_long.item.startswith(slugify(question, connectChar=' '))) & (db.idx_long.category == 'T')).select(
            db.answer.id, db.answer.fastinfo,
            join=[db.idx_join.on(db.idx_join.idx_long_id == db.idx_long.id),
                    db.answer.on(db.answer.id == db.idx_join.answer_id)],
        )
    book_rows = []
    for book in books:
        if book.fastinfo:
            book_dict = defaultdict(lambda: [])
            for ln in book.fastinfo.splitlines():
                if len(ln) > 1:
                    book_dict[ln[:1]].append(ln[1:])
            tit = '; '.join(book_dict['T'])
            aut = '; '.join(book_dict['A'])
            pub = '; '.join(book_dict['P'])
            puy = '; '.join(book_dict['Y'])
            book_rows.append([A(B(tit), ' ', SPAN(aut, _class="bg-info"), ' ', SPAN(pub, ' ', puy, _class="smaller"),
                                _class="list-group-item", _href=URL('impression', 'list', args=(question_id, book.id))),
                             tit, aut, pub, puy])
    locale.setlocale(locale.LC_ALL, COLLATING)
    book_rows.sort(key=lambda r: (locale.strxfrm(r[1]), locale.strxfrm(r[2]), locale.strxfrm(r[3]), r[4]))
    book_rows = [row[0] for row in book_rows]

    if book_rows:
        res_info = T("Vyber z nalezených publikací nebo ..")
    else:
        res_info = SPAN(EM(question), ' ... ', T("Publikace nebyla nalezena."))
    book_rows.append(DIV(
            DIV(res_info),
            DIV(
                A(T("Doplním popis (protože není v seznamu)"), _class="btn btn-info"),
                ' ',
                __btnCancelSearch(),
                _data_id="%s" % question_id),
            _class="well well-small"))
    retrieved_books = DIV(*book_rows, _class="list-group")
    return simplejson.dumps(retrieved_books.xml())

# ajax
#   called via button Zahodit click
@auth.requires_login()
def erase_question():
    db.question[request.args(0)] = dict(live=False)

def __btnCancelSearch(hidden=False):
    return A(T('Zahodit (nekatalogizovat)'), _id="erase_question", _href="#",
             _class="btn btn-info%s" % (' hidden' if hidden else ''))
