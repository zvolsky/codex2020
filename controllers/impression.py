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
            impression_id = db.impression.insert(answer_id=answer_id, owned_book_id=owned_book_id, iorder=last_order)
            db.impr_hist.insert(impression_id=impression_id, haction=1)

    fastinfo = db(db.answer.id == answer_id).select(db.answer.fastinfo).first().fastinfo
    return dict(form=form, impressions=db(current_book).select(), title=fastinfo.splitlines()[0][1:])

@auth.requires_login()
@auth.requires_signature()
def delete():
    answer_id = request.args(0)
    impression_id = request.args(1)
    if not impression_id:
        redirect(URL('default', 'index'))
    db.impr_hist.insert(impression_id=impression_id, haction=2)
    db(db.impression.id == impression_id).update(live=False)
    redirect(URL('list', args=(answer_id)))
