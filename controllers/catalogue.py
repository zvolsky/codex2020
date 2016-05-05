# -*- coding: utf-8 -*-

# ajax
#   called via setTimeout/ajax
#   maybe this can be redesigned as a component, using LOAD() and web2py_component(url,id) function
@auth.requires_login()
def retrieve_status():
    find_status = ''
    questions = db((db.question.live == True) & (db.question.auth_user_id == auth.user_id)).select(
            db.question.id, db.question.question, db.question.duration_marc,
            db.question.known, db.question.we_have, orderby=db.question.id)
    if questions:
        some_ready = False
        status_rows = []
        for q in questions:
            cls = 'list-group-item '
            if q.duration_marc is not None:
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
    def onvalidation(form):
        form.vars.asked = datetime.datetime.utcnow()

    form = SQLFORM(db.question)
    if form.process(onvalidation=onvalidation).accepted:
        scheduler.queue_task(task_catalogize,
                pvars={'question_id': form.vars.id, 'question': form.vars.question, 'asked': str(form.vars.asked)})
    return dict(form=form)
