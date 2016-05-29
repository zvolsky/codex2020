# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory


@auth.requires_login()
def list():
    question_id = request.args(0)
    answer_id = request.args(1)
    if not answer_id:
        redirect(URL('default', 'index'))

    current_book = db.impression.answer_id == answer_id

    form = SQLFORM.factory(
            Field('new', 'integer', default=1, label=T("Přidat"), comment=T("zadej počet nových výtisků")),
            hidden=dict(question_id=question_id),
            formstyle=formstyle_bootstrap3_compact_factory(),
            submit_button=T('Zařaď nové výtisky do knihovny')
            )
    form.add_button(T('Zpět ke katalogizaci'), URL('catalogue', 'find'))
    if form.process().accepted:
        db.question[question_id] = dict(live=False)  # question used: no longer display it

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

    answer = db(db.answer.id == answer_id).select(db.answer.ean, db.answer.fastinfo).first()
    ean = answer.ean[-3:]
    db.impression.fastid = Field.Virtual('fastid', lambda row: '%s-%s' % (ean, row.impression.iorder))
    return dict(form=form, impressions=db(current_book).select(), question_id=question_id,
                nnn=ean, title=answer.fastinfo.splitlines()[0][1:],
                fastid_title=T("RYCHLÁ IDENTIFIKACE KNIHY: Když se nepoužívají vlastní čarové kódy, vepiš toto číslo do výtisku - pak podle něj lze výtisk najít"))

@auth.requires_login()
@auth.requires_signature()
def delete():
    question_id = request.args(0)
    answer_id = request.args(1)
    impression_id = request.args(2)
    if not impression_id:
        redirect(URL('default', 'index'))
    db.impr_hist.insert(impression_id=impression_id, haction=2)
    db(db.impression.id == impression_id).update(live=False)
    redirect(URL('list', args=(question_id, answer_id)))
