# -*- coding: utf-8 -*-

from mzutils import shortened

from books import can_be_isxn, isxn_to_ean, parse_pubyear

from c2_db import ean_to_rik, publ_hash, answer_by_ean, answer_by_hash, make_fastinfo, get_libstyle
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
                    label=T("Vydání"), comment=T("číslo vydání (např.: 2.rozš.vyd. nebo: 3.vyd., v Odeonu 2.)")),
            submit_button = "Uložit a zadat výtisky",
            formstyle=formstyle_bootstrap3_compact_factory()
    )
    __btn_catalogue(form)
    if form.process().accepted:
        session.addbook = ['T' + eof_out(form.vars.title),   # title first (at least as it is displayed in impression/list)
                           't' + eof_out(form.vars.subtitle),
                           'E' + eof_out(form.vars.EAN),
                           'A' + eof_out(form.vars.authority, joiner='; '),
                           'P' + eof_out(form.vars.publisher, joiner='; '),
                           'p' + eof_out(form.vars.pubplace),
                           'Y' + eof_out(form.vars.pubyear),
                           'D' + eof_out(form.vars.edition),
                           ]
        redirect(URL('list', args=(question_id)))
    return dict(form=form)

@auth.requires_login()
def list():
    def existing_answer():
        flds = (db.answer.id,)
        if ean:
            row = answer_by_ean(db, ean, flds)
            if row:   # row exists...
                return row.id      # ...do not continue to find (using significant data) and do not insert
        # not found by isbn/ean
        row = answer_by_hash(db, md5publ, flds)
        if row:   # row exists...
            return row.id      # ...do not continue to find (using significant data) and do not insert
        return None

    def parse_descr(descr):
        """we have full description (valid for current library) and need ean+fastinfo+md5publ for (library independent) answer
        """
        descr_dict = {item[0]: item[1:].strip() for item in descr if len(item) > 1}
        ean = descr_dict.get('E', '')
        if ean:
            ean = isxn_to_ean(ean) if can_be_isxn(ean) else ''
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
    libstyle = get_libstyle()

    current_book = db.impression.answer_id == answer_id

    barcode = libstyle[3] == 'B'
    place = libstyle[4] == 'P'
    bill = session.bill and True or False
    form = SQLFORM.factory(
            Field('new', 'integer', default=1, label=T("Přidat"), comment=T("zadej počet nových výtisků")),
            Field('haction', 'string', length=2, default='+o',
                  requires=IS_IN_SET(HACTIONS_IN),
                  label=T("Získáno"), comment=T("jak byl/y výtisk/y pořízen/y")),
            Field('gift', 'boolean', default=False,
                  label=T("Dar"), comment=T("získáno darem")),
            Field('bill_id', db.bill,
                  requires=IS_EMPTY_OR(IS_IN_DB(db, db.bill.id, lambda row: row.htime.strftime('%d.%m.%Y %H:%M') + (', ' + no_our) if no_our else '')),
                  readable=bill, writable=False,
                  label=T("Doklad"), comment=T("doklad o pořízení (doklad lze změnit volbou Nový nákup/doklad)")),
            Field('not_this_bill', 'boolean', default=False,
                  readable=bill, writable=bill,
                  label=T("Není z dokladu"), comment=T("označením nebude u výtisku připsán výše uvedený doklad")),
            Field('barcode', 'string', length=16,
                  readable=barcode, writable=barcode,
                  label=T("Čarový kód"), comment=T("čarový kód (při více výtiscích bude číslo zvyšováno)")),
            Field('place_id', db.place,
                  requires=IS_EMPTY_OR(IS_IN_DB(db, db.place.id, '%(place)s')),
                  readable=place, writable=place,
                  label=T("Umístění"), comment=T("umístění výtisku")),
            Field('price_in', 'decimal(12,2)',
                  label=db.impression.price_in.label, comment=db.impression.price_in.comment),
            hidden=dict(question_id=question_id),
            formstyle=formstyle_bootstrap3_compact_factory(),
            submit_button=T('Zařaď nové výtisky do knihovny')
            )

    if bill:
        form.vars.bill_id = session.bill['id']
        if session.bill['gift']:
            form.vars.gift = True
            form.vars.haction = '+d'
        else:
            form.vars.haction = '+n'
        form.vars.loan = session.bill['loan'] and True or False

    if form.process().accepted:
        db.question[question_id] = dict(live=False)  # question used: no longer display it

        if answer_id:   # found in internet
            force_redirect = False
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
            lib_descr = db((db.lib_descr.answer_id == answer_id) & (db.lib_descr.descr == session.addbook)).select(db.lib_descr.id).first()
            if lib_descr:
                lib_descr_id = lib_descr.id
            else:
                lib_descr_id = db.lib_descr.insert(answer_id=answer_id, descr=session.addbook)
            # now we have both (answer, library description) and we can create library instance for this book
            owned_book_id = db.owned_book.insert(answer_id=answer_id, lib_descr_id=lib_descr_id)
            force_redirect = True  # because session.addbook was replaced with answer_id and URL need to change
        if 'addbook' in session:
            del session.addbook   # used, no need later for this

        rows = db((db.impression.library_id == auth.library_id) & (db.impression.answer_id == answer_id),
                    ignore_common_filters=True).select(db.impression.iorder, orderby=db.impression.iorder)
        iorders = [row.iorder for row in rows]
        iorder_candidate = 1
        barcode = form.vars.barcode and form.vars.barcode.strip() or ''
        incr_from = None
        for pos, _char in enumerate(barcode):
            if barcode[pos:].isdigit():
                incr_from = pos
                len_digits = len(barcode) - pos
                next_no = int(barcode[pos:])
                break
        for ii in xrange(form.vars.new):
            while iorder_candidate in iorders:
                iorder_candidate += 1
            if ii > 0 and incr_from is not None:
                next_no += 1
                barcode = barcode[:incr_from] + (len_digits * '0' + str(next_no))[len_digits:]
            bill_id = None if form.vars.not_this_bill else form.vars.bill_id
            impression_id = db.impression.insert(answer_id=answer_id, owned_book_id=owned_book_id,
                                                 iorder=iorder_candidate, gift=form.vars.gift, barcode=barcode,
                                                 place_id=form.vars.place_id,
                                                 bill_id=bill_id, price_in=form.vars.price_in)
            db.impr_hist.insert(impression_id=impression_id, haction=form.vars.haction, bill_id=bill_id)
            iorder_candidate += 1

        if force_redirect:
            redirect(URL(args=(question_id, answer_id)))

        form.add_button(T('Najít a zapsat další knihu z dokladu'), URL('catalogue', 'find'))
        form.add_button(T('Doklad je zpracován'), URL('bill_finished'))
    else:
        __btn_catalogue(form)

    db.impression.fastid = Field.Virtual('fastid', lambda row: '%s-%s' % (ean, row.impression.iorder))
    db.impr_hist._common_filter = lambda query: ~(db.impr_hist.haction.startswith('+'))
        # impressions with other manipulations as taking into db will have: db.impr_hist.id is not None
    impressions = db(current_book).select(db.impression.ALL, db.impr_hist.id, db.place.place,
                        orderby=db.impression.iorder,
                        left=[db.impr_hist.on(db.impr_hist.impression_id == db.impression.id),
                            db.place.on(db.place.id == db.impression.place_id)])
    return dict(form=form, impressions=impressions, question_id=question_id, answer_id=answer_id,
                libstyle=libstyle, shortened=shortened, nnn=ean, title=title,
                fastid_title=T("RYCHLÁ IDENTIFIKACE KNIHY: Výtisk rychle naleznete (nebo půjčíte) pomocí tohoto čísla nebo jen čísla před pomlčkou (což je konec čísla čarového kódu)."))

@auth.requires_login()
def bill_finished():
    if 'bill' in session:
        bill_id = session.bill['id']
        cnt_imp = db(db.impression.bill_id == bill_id).count()   # after removing impression as Mistake later, this count can stay higher
        db.bill[bill_id] = dict(cnt_imp=cnt_imp, imp_added=datetime.datetime.utcnow())
        del session.bill
    redirect(URL('manage', 'bills'))

@auth.requires_login()
@auth.requires_signature()
def displace():
    question_id = request.args(0)
    answer_id = request.args(1)
    impression_id = request.args(2)
    if not impression_id:
        redirect(URL('default', 'index'))
    db.impr_hist.insert(impression_id=impression_id, haction='--')
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

@auth.requires_login()
@auth.requires_signature()
def edit():
    impression_id = request.args(2)
    if not impression_id:
        redirect(URL('list'))
    libstyle = get_libstyle()
    db.impression.id.readable = False
    db.impression.iorder.readable = libstyle[1] == 'O'
    db.impression.barcode.readable = db.impression.barcode.writable = libstyle[3] == 'B'
    db.impression.place_id.readable = db.impression.place_id.writable = libstyle[4] == 'P'
    form = SQLFORM(db.impression, impression_id, submit_button=T("Uložit"), formstyle=formstyle_bootstrap3_compact_factory())
    form.add_button(T('Zpět (storno)'), URL('list', args=(request.args(0), request.args(1))))
    if form.process().accepted:
        redirect(URL('list', args=(request.args(0), request.args(1))))
    return dict(form=form)

def __btn_catalogue(form):
    form.add_button(T('Zpět ke katalogizaci'), URL('catalogue', 'find'))
