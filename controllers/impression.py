# -*- coding: utf-8 -*-

from mzutils import shortened

from books import can_be_isxn, isxn_to_ean, parse_pubyear, analyze_barcode, format_barcode, next_iid, next_sgn_imp

from dal_utils import get_libstyle

from c_utils import publ_hash, ean_to_fbi, make_fastinfo
from dal_utils import answer_by_ean, answer_by_hash
from c_db import PublLengths
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
            submit_button=T("Uložit a zadat výtisky"),
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
def list2():
    return list()

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
    extra = request.args(2)
    creatable = 0 if extra == 'done' else 1  # 1 form for adding, 0 without form but with form-show buttons after successfull adding
                                             # TODO: adapt this for -1 (extra=show): show list only (without any possibility to add)

    # get title+.. and rik to show book info
    if answer_id:
        answer = db(db.answer.id == answer_id).select(db.answer.ean, db.answer.rik, db.answer.fastinfo).first()
        title = answer.fastinfo.splitlines()[0][1:]
        rik = answer.rik
    else:
        if session.addbook:    # new book with local description only (from impression/description)
            fastinfo, ean, title, author, publisher, pubyear = parse_descr(session.addbook)
            rik = ean_to_fbi(ean)
        else:
            redirect(URL('default', 'index'))

    libstyle = get_libstyle()
    rik_width = libstyle['id'][3]
    rik_width = int(rik_width) if rik_width.isdigit() else 3
    rik_rendered = rik and rik[:rik_width][::-1] or ''  # rendered rik has always oposite order as db rik

    see_iid = libstyle['id'][0] == 'I'
    iid_part = int(libstyle['id'][1]) - 1  # for user: 0,1,2,.. ; but for autoinc we need -1,0,1,..
    see_sgn = libstyle['sg'][0] == 'G'
    if see_sgn:
        sgn_1 = libstyle['sg'][1]
        sgn_2 = libstyle['sg'][2]
        sgsep = libstyle['sgsep']
    see_barcode = libstyle['bc'][0] == 'B'
    barcode_inkr = libstyle['bc'][1] == '+'
    see_place = libstyle['gr'][0] == 'P'
    see_bill = session.bill and True or False
    '''
    buttons = [DIV(DIV(
                TAG.button(T('Zařaď nové výtisky do knihovny'), _type="submit", _class="btn btn-primary"),
                TAG.button(T('Zpět'), _type="button", _id="btn-done", _style="Xdisplay: none"),
                _class="btn-group-sm"), _class="col-sm-10 col-sm-offset-2")]
    #<button type="submit" class="btn btn-default">Zařaď nové výtisky do knihovny</button>
    #<input class="btn btn-primary" type="submit" value="Zařaď nové výtisky do knihovny">
    #<div class="col-sm-10 col-sm-offset-2"><div class="btn-group-sm"><input class="btn btn-primary" type="submit" value="Odeslat"></div></div>
    '''
    form = SQLFORM.factory(
            Field('new', 'integer', default=1, label=T("Přidat"), comment=T("zadej počet nových výtisků")),
            Field('haction', 'string', length=2, default='+o',
                  requires=IS_IN_SET(HACTIONS_IN),
                  label=T("Získáno"), comment=T("jak byl/y výtisk/y pořízen/y")),
            Field('gift', 'boolean', default=False,
                  label=T("Dar"), comment=T("získáno darem")),
            Field('bill', 'string', length=40, default=bill_format(session.bill),
                  readable=see_bill, writable=False,
                  label=T("Doklad"), comment=T("doklad o pořízení (doklad se zadává předem, volbou Nový nákup/doklad)")),
            Field('not_this_bill', 'boolean', default=False,
                  readable=see_bill, writable=see_bill,
                  label=T("Není z dokladu"), comment=T("označením nebude u výtisku připsán výše uvedený doklad")),
            Field('iid', 'string', length=PublLengths.iid,
                  readable=see_iid, writable=see_iid,
                  label=T("Přírůstkové číslo"), comment=T("přírůstkové číslo")),
            Field('sgn', 'string', length=PublLengths.sgn,
                  readable=see_sgn, writable=see_sgn,
                  label=T("Signatura"), comment=T("signatura výtisku")),
            Field('barcode', 'string', length=PublLengths.barcode,
                  readable=see_barcode, writable=see_barcode,
                  label=T("Čarový kód"), comment=T("čarový kód (při více výtiscích bude číslo zvyšováno)")),
            Field('place_id', db.place,
                  requires=IS_EMPTY_OR(IS_IN_DB(db, db.place.id, '%(place)s')),
                  readable=see_place, writable=see_place,
                  label=T("Umístění"), comment=T("umístění výtisku")),
            Field('price_in', 'decimal(12,2)',
                  label=db.impression.price_in.label, comment=db.impression.price_in.comment),
            hidden=dict(question_id=question_id),
            submit_button=T('Zařaď nové výtisky do knihovny'),
            formstyle=formstyle_bootstrap3_compact_factory(),
            )

    if see_bill:
        if session.bill['gift']:
            form.vars.gift = True
            form.vars.haction = '+d'
        else:
            form.vars.haction = '+n'
        form.vars.loan = session.bill['loan'] and True or False

    if form.process().accepted:
        creatable = 0  # hide the form and instead display the form-show button
        db.question[question_id] = dict(live=False)  # question used: no longer display it

        if answer_id:   # found in internet
            force_redirect = False
            owned_book = db((db.owned_book.answer_id == answer_id) & (db.owned_book.library_id == auth.library_id),
                            ignore_common_filters=True).select(db.owned_book.id).first()
                        # ignore_common_filters off, as long it will contain cnt>0
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
                answer_id = db.answer.insert(md5publ=md5publ, ean=ean, rik=rik, fastinfo=fastinfo,
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
        iid = form.vars.iid
        sgn_imp = sgn = form.vars.sgn
        if sgn and sgn_1:
            sgn_imp += sgsep + sgn_1
        barcode = form.vars.barcode and form.vars.barcode.strip()
        incr_from, len_digits, barcode_no = analyze_barcode(barcode)
        for ii in xrange(form.vars.new):
            while iorder_candidate in iorders:
                iorder_candidate += 1
            if ii:  # 2nd added impression and all next
                iid = next_iid(iid, iid_part, maxlen=PublLengths.iid)
                sgn_imp, sgn_2 = next_sgn_imp(sgn, sgsep, sgn_2, maxlen=PublLengths.sgn)
                if barcode and barcode_inkr:
                    barcode_no += 1
                    barcode = format_barcode(barcode, incr_from, len_digits, barcode_no)
                else:
                    barcode = None
            bill_id = None if form.vars.not_this_bill else session.bill and session.bill['id']
            htime = datetime.datetime.utcnow()
            impression_id = db.impression.insert(answer_id=answer_id, owned_book_id=owned_book_id,
                                                 iorder=iorder_candidate, gift=form.vars.gift,
                                                 iid=iid, sgn=sgn_imp, barcode=barcode,
                                                 htime=htime, haction=form.vars.haction,
                                                 place_id=form.vars.place_id, price_in=form.vars.price_in)
            db.impr_hist.insert(impression_id=impression_id, haction=form.vars.haction, bill_id=bill_id)
            iorder_candidate += 1

        if force_redirect:
            redirect(URL(args=(question_id, answer_id)))

    if creatable == 0:
        form.add_button(T('Zpět'), URL(args=request.args[:2] + ['done']))
    __btn_catalogue(form)

    db.impression.rik = Field.Virtual('rik', lambda row: '%s-%s' % (rik_rendered, row.impression.iorder))
    db.impr_hist._common_filter = lambda query: ~(db.impr_hist.haction.startswith('+'))
        # impressions with other manipulations as taking into db will have: db.impr_hist.id is not None
    impressions = db(db.impression.answer_id == answer_id).select(
                        db.impression.ALL, db.impr_hist.id, db.place.place,
                        orderby=db.impression.iorder,
                        left=[db.impr_hist.on(db.impr_hist.impression_id == db.impression.id),
                            db.place.on(db.place.id == db.impression.place_id)])    # db.bill.no_our,
    return dict(form=form, impressions=impressions, question_id=question_id, answer_id=answer_id,
                libstyle=libstyle, shortened=shortened, rik=rik_rendered, title=title,
                creatable=creatable, see_bill=see_bill,
                rik_title=T("RYCHLÁ IDENTIFIKACE KNIHY: Výtisk rychle naleznete (nebo půjčíte) pomocí tohoto čísla nebo jen čísla před pomlčkou (což je konec čísla čarového kódu)."))

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
    db.impression.iid.readable = db.impression.iid.writable = libstyle['id'][0] == 'I'
    db.impression.sgn.readable = db.impression.sgn.writable = libstyle['sg'][0] == 'G'
    db.impression.iorder.readable = libstyle['id'][2] == 'O'
    db.impression.barcode.readable = db.impression.barcode.writable = libstyle['bc'][0] == 'B'
    db.impression.place_id.readable = db.impression.place_id.writable = libstyle['gr'][0] == 'P'
    form = SQLFORM(db.impression, impression_id, submit_button=T("Uložit"), formstyle=formstyle_bootstrap3_compact_factory())
    form.add_button(T('Zpět (storno)'), URL('list', args=(request.args(0), request.args(1))))
    if form.process().accepted:
        redirect(URL('list', args=(request.args(0), request.args(1))))
    return dict(form=form)

def __btn_catalogue(form):
    form.add_button(T('Zpět ke katalogizaci'), URL('catalogue', 'find'))
