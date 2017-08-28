# -*- coding: utf-8 -*-

import locale

from gluon.contrib import simplejson

from mzutils import slugify
from plugin_mz import formstyle_bootstrap3_compact_factory

from books import can_be_isxn, isxn_to_ean

from c_utils import parse_fastinfo
from c2_common import get_book_line


COLLATING = 'cs_CZ.utf8'
ISMN1 = '979-0-'
ISBN1 = '80-'
EAN1 = '97880'
EAN2 = '97980'


@auth.requires_login()
def find():
    def onvalidation(form):
        if EAN1 and request.vars.question.isdigit() and len(EAN1 + request.vars.question) == 13:
            form.vars.question = EAN1 + request.vars.question
        form.vars.asked = datetime.datetime.utcnow()

    comment = T("sejmi **prodejní čarový kód EAN**, chybí-li, stiskni **F7** a opiš **ISBN** nebo zadej **počáteční 2-3 slova názvu**")
    if EAN1:
        comment += ' ' + "''" + T('(EAN z klávesnice: stiskni F8 (F9) nebo jen opiš posledních %s číslic za %s)') % (13 - len(EAN1), EAN1) + "''"
    db.question.question.comment = MARKMIN(comment)

    form = SQLFORM(db.question, hidden=dict(f6=ISMN1, f7=ISBN1, f8=EAN1, f9=EAN2), formstyle=formstyle_bootstrap3_compact_factory())
    if form.process(onvalidation=onvalidation).accepted:
        if DEBUG_SCHEDULER:
            task_catalogize(form.vars.id, form.vars.question, str(form.vars.asked))  # debug
        else:
            scheduler.queue_task(task_catalogize,
                    pvars={'question_id': form.vars.id, 'question': form.vars.question, 'asked': str(form.vars.asked)},
                    timeout=300, immediate=True)
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
    question, isxn_like = __get_question(question_id)
    if isxn_like:
        ean = isxn_to_ean(question)
        query = db.answer.ean == ean
        books = db(query).select(db.answer.id, db.answer.fastinfo)
        my_books = db((db.owned_book.id > 0) & query).select(db.answer.id, db.answer.fastinfo,
                                                             join=db.answer.on(db.answer.id == db.owned_book.answer_id))
    else:
        if ',' in question:
            query = (db.idx_long.item.startswith(slugify(question, connectChar=' '))) & (db.idx_long.category.belongs(('T', 'A')))
        else:
            query = (db.idx_long.item.startswith(slugify(question, connectChar=' '))) & (db.idx_long.category == 'T')
        books = db(query).select(
            db.answer.id, db.answer.fastinfo, distinct=True,
            join=[db.idx_join.on(db.idx_join.idx_long_id == db.idx_long.id),
                    db.answer.on(db.answer.id == db.idx_join.answer_id)],
        )
        my_books = db((db.owned_book.id > 0) & query).select(db.answer.id, db.answer.fastinfo, distinct=True,
            join=[db.answer.on(db.answer.id == db.owned_book.answer_id),
                    db.idx_join.on(db.idx_join.answer_id == db.answer.id),
                    db.idx_long.on(db.idx_long.id == db.idx_join.idx_long_id)],
        )

    locale.setlocale(locale.LC_ALL, COLLATING)

    book_rows = []
    for book in my_books.find(lambda row: row.fastinfo):
        __book_to_list(book_rows, book, question_id)
    book_rows = __sort_book_rows(book_rows)
    my_books_ids = [book.id for row in my_books]
    if book_rows:
        book_rows.insert(0, DIV(T("Naše knihy"), _class="alert alert-sm alert-info"))

    ext_rows = []
    for book in books.find(lambda row: row.id not in my_books_ids and row.fastinfo):
        __book_to_list(ext_rows, book, question_id)

    if ext_rows:
        if book_rows:  # show this as separator from 'Our books' only if there is some book from outside
            book_rows.append(P())
            book_rows.append(DIV(T("Ze souborného katalogu"), _class="alert alert-sm alert-info"))
        book_rows = book_rows + __sort_book_rows(ext_rows)

    if book_rows or my_books:
        res_info = T("Vyber z nalezených publikací nebo ..")
    else:
        res_info = SPAN(EM(question), ' ... ', T("Publikace nebyla nalezena."))
    book_rows.append(DIV(
            DIV(res_info),
            DIV(
                A(T("Doplním popis (protože není v seznamu)"), _class="btn btn-info",
                        _href="%s" % URL('impression', 'description', args=(question_id))),
                ' ',
                __btnCancelSearch(),
                _data_id="%s" % question_id),  # maybe can be a level down by the Cancel btn, but let this working solution
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

def __get_question(question_id):
    question = db(db.question.id == question_id).select(db.question.question, cache=(cache.ram, 1800), cacheable=True).first().question
    return question, can_be_isxn(question)

def __book_to_list(book_rows, book, question_id):
    tit, aut, pub, puy = parse_fastinfo(book.fastinfo)
    book_line = get_book_line(tit, aut, pub, puy)
    book_rows.append([A(*book_line, _class="list-group-item", _href=URL('impression', 'list', args=(question_id, book.id))),
                     tit, aut, pub, puy])

def __sort_book_rows(book_rows):
    book_rows.sort(key=lambda r: (locale.strxfrm(r[1]), locale.strxfrm(r[2]), locale.strxfrm(r[3]), r[4]))
    return [row[0] for row in book_rows]
