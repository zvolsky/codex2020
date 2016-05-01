# -*- coding: utf-8 -*-

from c2_z39 import get_from_large_library
from c2_marc import parse_Marc_and_updatedb


# called from find() action and via setTimeout/ajax
# maybe this can be redesigned as a component, using LOAD() and web2py_component(url,id) function
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
        warning, results = get_from_large_library(form.vars.question)
        if warning:
            response.flash = warning
        else:
            retrieved, inserted = parse_Marc_and_updatedb(results)
            db.question[form.vars.id] = {'answered': datetime.datetime.now(), 'retrieved': retrieved, 'inserted': inserted}
            response.flash = T('%s staženo, z toho nových: %s') % (retrieved, inserted)
    return dict(form=form, retrieve_status=retrieve_status())

def xfind():
    rc, user_key = redis_user(auth)
    form = SQLFORM.factory(
            Field('starter', 'string', length=20, label=T("Zkus najít podle"),
                comment=T("počáteční 2-3 slova názvu nebo sejmi EAN čarový kód pro vyhledání publikace")))
    if form.process().accepted:
        fnd = form.vars.starter  # .strip() ?
        if fnd and len(fnd) >= 3:
            qkey = user_key + 'Q'
            rc.rpush(qkey, fnd)
        else:
            response.flash = T("Zadej alespoň 3 znaky pro vyhledání.")
    questions = []
    for q in rc.lrange(user_key + 'Q', 0, -1):
        is_in_hash = True if 'neco' in q else False
        questions.append((q, is_in_hash))
    return dict(form=form, questions=questions)
    # LSET nesmysl + LREM pro odstranění zprostřed

