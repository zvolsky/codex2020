# -*- coding: utf-8 -*-

from books import can_be_isxn, isxn_to_ean, parse_pubyear

from c2_db import ean_to_rik, publ_hash, answer_by_ean, answer_by_hash, make_fastinfo
from plugin_mz import formstyle_bootstrap3_compact_factory


@auth.requires_login()
def description():
    def eof_out(txt, joiner=' '):
        txt = txt.replace('\t', '').replace('\r', '')
        return joiner.join((ln.strip() for ln in txt.splitlines() if ln))

    question_id = request.args(0)
    form = SQLFORM.factory(
            Field('title', 'text',
                    requires = IS_NOT_EMPTY(),
                    label=T("Název"), comment=T("název knihy (titul)")),
            Field('subtitle', 'text',
                    label=T("Podnázev"), comment=T("podnázev (doplňující část názvu)")),
            Field('EAN', 'string', length=18,
                    label=T("EAN/ISBN"), comment=T("EAN (čarový kód, vytištěný na knize) případně ISBN, není-li EAN vytištěn")),
            Field('authority', 'text',
                    label=T("Autor"), comment="autor (Příjmení, Jméno); PŘI VÍCE AUTORECH ČTI POKYN NAHOŘE !"),
            Field('publisher', 'text',
                    label=T("Nakladatel"), comment="nakladatel (bez sídla); PŘI VÍCE NAKLADATELÍCH ČTI POKYN NAHOŘE !"),
            Field('pubplace', 'text',
                    label=T("Místo vydání"), comment="místo vydání"),
            Field('pubyear', 'text',
                    label=T("Rok vydání"), comment=T("rok vydání")),
            Field('edition', 'text',
                    label=T("Vydání"), comment=T("číslo vydání (a případně podrobnější informace)")),
            submit_button = "Uložit a zadat výtisky",
            formstyle=formstyle_bootstrap3_compact_factory()
    )
    __btn_catalogue(form)
    if form.process().accepted:
        session.addbook = ['T' + eof_out(form.vars.title),   # title first (at least as it is displayed in impression/list)
                           't' + eof_out(form.vars.title),
                           'E' + eof_out(form.vars.EAN),
                           'A' + eof_out(form.vars.authority, joiner='; '),
                           'P' + eof_out(form.vars.publisher, joiner='; '),
                           'p' + eof_out(form.vars.pubplace),
                           'Y' + eof_out(form.vars.pubyear),
                           'D' + eof_out(form.vars.edition),
                           ]
        redirect(URL('list', args(question_id)))
    return dict(form=form)

@auth.requires_login()
def list():
    def existing_answer():
        flds = (db.answer.id,)
        if ean:
            row = answer_by_ean(ean, flds)
            if row:   # row exists...
                return row.id      # ...do not continue to find (using significant data) and do not insert
        # not found by isbn/ean
        row = answer_by_hash(md5publ, flds)
        if row:   # row exists...
            return row.id      # ...do not continue to find (using significant data) and do not insert
        return None

    def parse_descr(descr):
        """we have full description (valid for current library) and need ean+fastinfo+md5publ for (library independent) answer
        """
        descr_dict = {item[0]: item[1:].strip() for item in descr if len(item) > 1}
        ean = descr_dict.get('E', '')
        if ean:
            ean = isxn_to_ean(question) if can_be_isxn(ean) else ''
        title = ' : '.join(filter(lambda a: a, (descr_dict.get('T', ''), descr_dict.get('t', ''))))
        author = descr_dict.get('A', '')
        publisher = ' : '.join(filter(lambda a: a, (descr_dict.get('p', ''), descr_dict.get('P', ''))))
        pubyear = descr_dict.get('Y', '')
        fastinfo = make_fastinfo(title, author, publisher, pubyear)
        return fastinfo, ean, title, author, publisher, pubyear

    question_id = request.args(0)
    answer_id = request.args(1)
    if answer_id:
        answer = db(db.answer.id == answer_id).select(db.answer.ean, db.answer.fastinfo).first()
        ean = answer.ean[-3:]
        title = answer.fastinfo.splitlines()[0][1:]
    else:
        if session.addbook:    # new book with local description only (from impression/description)
            fastinfo, ean, title, author, publisher, pubyear = parse_descr(session.addbook)
        else:
            redirect(URL('default', 'index'))

    current_book = db.impression.answer_id == answer_id

    form = SQLFORM.factory(
            Field('new', 'integer', default=1, label=T("Přidat"), comment=T("zadej počet nových výtisků")),
            hidden=dict(question_id=question_id),
            formstyle=formstyle_bootstrap3_compact_factory(),
            submit_button=T('Zařaď nové výtisky do knihovny')
            )
    __btn_catalogue(form)
    if form.process().accepted:
        del session.addbook   # we have this in fastinfo
        db.question[question_id] = dict(live=False)  # question used: no longer display it

        if answer_id:   # found in internet
            owned_book = db(db.owned_book.answer_id == answer_id).select(db.owned_book.id).first()
            if owned_book:
                owned_book_id = owned_book.id
            else:
                owned_book_id = db.owned_book.insert(answer_id=answer_id)
        else:           # new book with local description only (from impression/description)
            # we already have parsed local description here: fastinfo + title, author, publisher, pubyear
            md5publ = publ_hash(title, author, publisher, pubyear)
            # do we have answer?
            answer_id = existing_answer()  # check by ean, md5publ
            if answer_id is None:
                pubyears = parse_pubyear(pubyear)
                answer_id = db.answer.insert(md5publ=md5publ, ean=ean, rik=ean_to_rik(ean), fastinfo=fastinfo,
                                             year_from=pubyears[0], year_to=pubyears[1])
            # do we have this library description?
            lib_descr = db((db.lib_descr.answer_id == answer_id) & (db.lib_descr.descr == descr)).select(db.lib_descr.id).first()
            if lib_descr:
                lib_descr_id = lib_descr.id
            else:
                lib_descr_id = db.lib_descr.insert(answer_id=answer_id, descr=descr)
            # now we have both (answer, library description) and we can create library instance for this book
            owned_book_id = db.owned_book.insert(answer_id=answer_id, lib_descr_id=lib_descr_id)

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

    db.impression.fastid = Field.Virtual('fastid', lambda row: '%s-%s' % (ean, row.impression.iorder))
    db.impr_hist._common_filter = lambda query: db.impr_hist.haction > 1
        # impressions with other manipulations as taking into db will have: db.impr_hist.id is not None
    impressions = db(current_book).select(db.impression.ALL, db.impr_hist.id,
                        orderby=db.impression.iorder,
                        left=db.impr_hist.on(db.impr_hist.impression_id == db.impression.id))
    return dict(form=form, impressions=impressions, question_id=question_id,
                nnn=ean, title=title,
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

def __btn_catalogue(form):
    form.add_button(T('Zpět ke katalogizaci'), URL('catalogue', 'find'))
