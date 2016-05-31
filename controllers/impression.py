# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory


@auth.requires_login()
def description():
    question_id = request.args(0)
    form = SQLFORM.factory(
            Field('title', 'text',
                    label=T("Název"), comment=T("název knihy (titul)")),
            Field('subtitle', 'text',
                    label=T("Podnázev"), comment=T("podnázev (doplňující část názvu)")),
            Field('EAN', 'string', length=18,
                    label=T("EAN/ISBN"), comment=T("EAN (čarový kód, vytištěný na knize) nebo ISBN")),
            Field('authority', 'text',
                    label=T("Autor"), comment="Uveď KAŽDÉHO autora na VLASTNÍM řádku takto: Příjmení, Jméno"),
            Field('publisher', 'text',
                    label=T("Nakladatel"), comment="Uveď nakladatele takto: Jméno, Sídlo (dalšího nakladatele můžeš uvést na další řádek)"),
            Field('pubyear', 'text',
                    label=T("Rok vydání"), comment=T("rok vydání")),
            Field('edition', 'text',
                    label=T("Vydání"), comment=T("číslo vydání (a případně podrobnější informace)")),
    )
    if form.process().accepted:
        pass
    return dict(form=form)

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

        rows = db((db.impression.library_id == auth.library_id) & (db.impression.answer_id == answer_id),
                    ignore_common_filters=True).select(db.impression.iorder, orderby=db.impression.iorder)
        iorders = [row.iorder for row in rows]
        iorder_candidate = 1
        for ii in xrange(form.vars.new):
            while iorder_candidate in iorders:
                iorder_candidate += 1
            impression_id = db.impression.insert(answer_id=answer_id, owned_book_id=owned_book_id, iorder=iorder_candidate)
            db.impr_hist.insert(impression_id=impression_id, haction=1)
            iorder_candidate += 1

    answer = db(db.answer.id == answer_id).select(db.answer.ean, db.answer.fastinfo).first()
    ean = answer.ean[-3:]
    db.impression.fastid = Field.Virtual('fastid', lambda row: '%s-%s' % (ean, row.impression.iorder))
    db.impr_hist._common_filter = lambda query: db.impr_hist.haction > 1
        # impressions with other manipulations as taking into db will have: db.impr_hist.id is not None
    impressions = db(current_book).select(db.impression.ALL, db.impr_hist.id,
                        orderby=db.impression.iorder,
                        left=db.impr_hist.on(db.impr_hist.impression_id == db.impression.id))
    return dict(form=form, impressions=impressions, question_id=question_id,
                nnn=ean, title=answer.fastinfo.splitlines()[0][1:],
                fastid_title=T("RYCHLÁ IDENTIFIKACE KNIHY: Výtisk rychle naleznete (nebo půjčíte) pomocí tohoto čísla nebo jen čísla před pomlčkou (což je konec čísla čarového kódu)."))

@auth.requires_login()
@auth.requires_signature()
def displace():
    question_id = request.args(0)
    answer_id = request.args(1)
    impression_id = request.args(2)
    if not impression_id:
        redirect(URL('default', 'index'))
    db.impr_hist.insert(impression_id=impression_id, haction=2)
    db(db.impression.id == impression_id).update(live=False)
    redirect(URL('list', args=(question_id, answer_id)))

@auth.requires_login()
@auth.requires_signature()
def mistake():
    question_id = request.args(0)
    answer_id = request.args(1)
    impression_id = request.args(2)
    if not impression_id:
        redirect(URL('default', 'index'))
    db(db.impression.id == impression_id).delete()
    redirect(URL('list', args=(question_id, answer_id)))
