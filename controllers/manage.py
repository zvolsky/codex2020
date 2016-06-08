# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory


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
    db.bill.id.readable = False
    grid = SQLFORM.grid(db.bill,
            formstyle=formstyle_bootstrap3_compact_factory(),
            showbuttontext=False,
            )
    return dict(grid=grid)

@auth.requires_login()
def new_bill():
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
