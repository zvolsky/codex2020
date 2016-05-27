# -*- coding: utf-8 -*-

@auth.requires_login()
def list():
    answer_id = request.args(0)
    if not answer_id:
        redirect(URL('default', 'index'))

    current_book = db.impression.answer_id == answer_id

    form = SQLFORM.factory(
            Field('new', 'integer', default=1, label=T("Přidat"), comment=T("zadej počet nových výtisků")),
            submit_button=T('Zařaď nové výtisky do knihovny')
            )
    if form.process().accepted:
        owned_book = db(db.owned_book.answer_id == answer_id).select(db.owned_book.id).first()
        if owned_book:
            owned_book_id = owned_book.id
        else:
            owned_book_id = db.owned_book.insert(answer_id=answer_id)

        max = db.impression.iorder.max()
        last_order = db(current_book).select(max).first()[max] or 0
        for ii in xrange(form.vars.new):
            last_order += 1
            db.impression.insert(answer_id=answer_id, owned_book_id=owned_book_id, iorder=last_order)

    return dict(form=form, impressions=db(current_book).select())

@auth.requires_login()
def delete():
    db(db.impression.id == request.args(0)).delete()
    redirect(URL('list'))
