# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory

from c2_db import finish_bill


@auth.requires_login()
def partners():
    db.partner.id.readable = False
    grid = SQLFORM.grid(db.partner,
            formstyle=formstyle_bootstrap3_compact_factory(),
            showbuttontext=False,
            csv=False
            )
    return dict(grid=grid)

@auth.requires_login()
def bills():
    # handle inconsistecies in bills - fix count of impressions + close all except the last one
    opened = db(db.bill.imp_added == None).select()
    skip_idx = len(opened) - 1  # do not close this bill
    for idx, bill in enumerate(opened):
        fix = {'cnt_imp': db(db.impr_hist.bill_id == bill.id).count()}
        if idx == skip_idx:
            session.bill = bill.as_dict()  # if session will break, listing of bills will reopen the last one
        else:
            fix['imp_added'] = datetime.datetime.utcnow()
        bill.update_record(**fix)

    db.bill.id.readable = False
    grid = SQLFORM.grid(db.bill,
            formstyle=formstyle_bootstrap3_compact_factory(),
            showbuttontext=False,
            links=[{'header': T("Položky"), 'body': lambda row: A('xxx')}]
            )
    return dict(grid=grid)

@auth.requires_login()
def new_bill():
    last_bill = db(db.bill).select(db.bill.no_our, orderby=~db.bill.htime, limitby=(0, 1)).first()
    last_bill_no = last_bill and last_bill.no_our
    if last_bill_no:
        db.bill.no_our.comment = '%s %s; ' % (last_bill_no, T("předcházelo")) + db.bill.no_our.comment

    db.bill.cnt_imp.readable = False
    db.bill.imp_added.readable = False
    form = SQLFORM(db.bill, submit_button=T("Uložit"), formstyle=formstyle_bootstrap3_compact_factory())
    if form.process().accepted:
        gohome = True
        if form.vars.take_in and (form.vars.loan is None or form.vars.loan == '+f'):
            session.bill = db(db.bill.id == form.vars.id).select().first().as_dict()
            redirect(URL('catalogue', 'find'))
        elif form.vars.loan == '-f':
            session.flash = "Výtisky vyřaďte ze seznamu výtisků (Meziknihovní zápůjčky zatím nejsou provázány s výtisky)"
        elif 'o' in form.vars.loan:
            session.flash = "Meziknihovní zápůjčky zatím nejsou podporovány - můžete řešit vytvořením 'čtenáře' a výpůjčkou"
        elif form.vars.loan == '+f':
            response.flash = T("Prosím, označte ještě Příjem")  # +f bez označení příjmu TODO: validace
            gohome = False
        else:
            session.flash = "Výtisky vyřaďte ze seznamu výtisků (Výdej knih na doklad zatím není provázán s výtisky)"
        if 'bill' in session:
            del session.bill
        if gohome:
            redirect(URL('default', 'index'))
    return dict(form=form)

@auth.requires_login()
def bill_finished():
    if 'bill' in session:
        finish_bill(session.bill['id'])
    redirect(URL('bills'))
