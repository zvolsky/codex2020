# -*- coding: utf-8 -*-

from c2_z39 import get_from_large_library
from c2_marc import parse_Marc_and_updatedb


# ajax
#   called via setTimeout/ajax
#   maybe this can be redesigned as a component, using LOAD() and web2py_component(url,id) function
@auth.requires_login()
def retrieve_status():
    find_status = ''
    questions = db((db.question.live == True) & (db.question.auth_user_id == auth.user_id)).select(
            db.question.id, db.question.question, db.question.answered,
            db.question.known, db.question.we_have, orderby=db.question.id)
    if questions:
        some_ready = False
        status_rows = []
        for q in questions:
            cls = 'list-group-item '
            if q.answered:
                cls += 'list-group-item-success active'
                some_ready = True
            else:
                cls += 'disabled'
            status_rows.append(A(SPAN(q.we_have or 0, _class="badge"), SPAN(q.known or 0, _class="badge"), q.question, _href='#', _class=cls))
        if some_ready:
            hint = T("Vyber vyhledanou knihu ke katalogizaci nebo zadej další")
        else:
            hint = T("Počkej na vyhledání předchozího zadání nebo zadej další knihu ke zpracování")
        find_status = SPAN(hint, _class="help-block") + DIV(*status_rows, _class="list-group", _style="max-width: 500px;")
    return find_status

@auth.requires_login()
def find():
    form = SQLFORM(db.question)
    if form.process().accepted:
        need_find = form.vars.id
    else:
        need_find = ''
    return dict(form=form, need_find=need_find)

# ajax
@auth.requires_login()
def find_worker():
    """the time consuming retrieve/parse/db-save action
    in fact we call 2 actions from find():
        - via form submit: same action find() will repeat here (finished fast),
        - via data in hidden .html element/on-document-ready/ajax (time consuming action)

    we use ajax instead of real threading because threading is not good idea from inside the web server
        (because not we but web server has full control over creating/destroying processes/threads)

    maybe web server timeout need to be increased like for nginx (increase from 60s):
        http
        {
          server
          {
            …
            location /
            {
                 …
                 proxy_read_timeout 180s;
    """
    question_id = int(request.args[0])
    question = db.question[question_id]  # we could avoid this db access (giving value to browser and back),
                                         # however this has better security (int, not answered) and no need for dig.signat.
    if question and not question.answered:
        warning, results = get_from_large_library(question.question)
        if not warning:
            #    response.flash = warning
            #else:
            retrieved, inserted = parse_Marc_and_updatedb(results)
            db.question[int(question_id)] = {'answered': datetime.datetime.now(), 'retrieved': retrieved, 'inserted': inserted}
    return ''  # dummy result here
