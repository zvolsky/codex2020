# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory
from dal_common import hide_all_fields
# from dal_common import ...  # in choose_library()

@auth.requires_login()
def choose_library():
    """
        request.args(0): missing: Show, 'all': ShowAll, '<id>': Set
    """
    from dal_common import get_my_libraries_with_names, get_all_libraries

    def set_this(library_id):
        session.library_id = library_id
        redirect(URL('default', 'index'))

    spec_request = request.args(0)
    admin = auth.has_membership('admin')
    active = accessible = None
    my_rw = []
    my_ro = []

    my_libraries = get_my_libraries_with_names()

    if spec_request:
        if spec_request == 'all':
            accessible = get_all_libraries(admin=admin,
                                           exclude_ids=[library.library.id for library in my_libraries])
        else:     # Set the library
            if admin:
                row = db(db.library.id == spec_request).select(db.library.id).first()
                if row:
                    set_this(row.id)
            else:
                for row in my_libraries:
                    if str(row.library.id) == spec_request:
                        set_this(row.library.id)  # contains redirect

    if session.library_id:
        row = db(db.library.id == session.library_id).select(db.library.library).first()
        if row:
            active = row.library   # for admin this is not always inside the next cycle
    for library in my_libraries:
        if not active and library.auth_lib.rw:
            session.library_id = library.library.id
            active = library.library.library
        elif active and session.library_id == library.library.id:
            pass
        elif library.auth_lib.rw:
            my_rw.append(library)
        else:
            my_ro.append(library)

    return dict(active=active, my_rw=my_rw, my_ro=my_ro, accessible=accessible, admin=admin)


@auth.requires_login()
def new():
    """will create a library"""
    hide_all_fields(db.library)
    db.library.library.writable = db.library.library.readable = True
    db.library.ltype.writable = db.library.ltype.readable = True

    form = SQLFORM(db.library,
                   formstyle=formstyle_bootstrap3_compact_factory(),
                   submit_button=T("Vytvořit knihovnu"))
    if not auth.library_id:
        form.vars.library = T("zkušební") + ' ' + auth.user.username
    if form.process().accepted:
        __clear_libstyle()
        auth_lib_id = db.auth_lib.insert(auth_user_id=auth.user_id, library_id=form.vars.id, rw=True)
        now = datetime.datetime.now()
        db.lib_rights.insert(auth_lib_id=auth_lib_id, allowed='W', given=now)
        db.lib_rights.insert(auth_lib_id=auth_lib_id, allowed='A', given=now)
        auth.library_id = form.vars.id
        redirect(URL('library', args='home'))
    return dict(form=form)


def library():
    """edit library info"""
    if not auth.library_id or not auth.user_id:
        redirect(URL('choose_library'))
    important = db(db.library.id == auth.library_id).select(db.library.imp_system).first()
    if not important:
        redirect(URL('choose_library'))
    ownership = db((db.auth_lib.auth_user_id == auth.user_id) & (db.auth_lib.library_id == auth.library_id) & (db.auth_lib.rw == True)).select().first()
    if not ownership:
        redirect(URL('choose_library'))

    section = request.args(0) or 'home'

    hide_all_fields(db.library)
    if section == 'home':
        db.library.library.writable = db.library.library.readable = True
        db.library.street.writable = db.library.street.readable = True
        db.library.city.writable = db.library.city.readable = True
        db.library.plz.writable = db.library.plz.readable = True
        db.library.ltype.writable = db.library.ltype.readable = True
    elif section == 'software':
        db.library.old_system.writable = db.library.old_system.readable = True
        db.library.imp_system.writable = db.library.imp_system.readable = True

    '''
    Field('slug', 'string', length=32,
          requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'library.slug')],
          label=T("URL jméno"),
          comment=T("jméno do URL adresy [malá písmena, číslice, pomlčka/podtržítko] (příklad: petr_stary_kladno)")),
    Field('read_pwd', 'password',
          label=T("Heslo pro čtení"), comment=T("ponechej prázdné pro veřejně přístupný katalog")),
    Field('created', 'datetime', default=datetime.datetime.utcnow(),
          notnull=True, writable=False,
          label=T("Vytvořeno"), comment=T("čas vytvoření evidence")),
    Field('completed', 'date',
          label=T("Dokončeno"), comment=T("datum dokončení zápisu fondu knihovny")),
    Field('review_date', 'date', default=datetime.date.today(),
          notnull=True, requires=[IS_NOT_EMPTY(), IS_DATE(format=T('%d.%m.%Y'))],
          label=T("Zahájení revize"), comment=T("den zahájení revize (vypíší se výtisky, nenalezené od tohoto data)")),
    Field('st_imp_id', 'boolean', notnull=True, default=False,  # libstyle['id'][0] = I
          label=T("Přír.číslo ?"), comment=T("označte, pokud knihovna používá přírůstková čísla výtisků")),
    Field('st_imp_idx', 'integer', notnull=True, default=1,
          # libstyle['id'][1] = 0|1|2|.. which number-part of ID should be incremented
          label=T("Typ inkrementování"), comment=T(
            "0 nezvětšovat přír.číslo; 1 zvětšovat resp. zvětšovat první nalezené číslo; 2 zvětšovat druhé nalezené podčíslo (např. při stylu: rok/číslo)")),
    Field('st_imp_ord', 'boolean', notnull=True, default=False,  # libstyle['id'][2] = O
          label=T("Čís.výtisku ?"),
          comment=T("označte, pokud se má zobrazovat číslo výtisku jako rozlišení výtisků každé publikace")),
    Field('st_imp_rik', 'integer',  # libstyle['lrik'] = 2/3/4/5/6
          notnull=True, default=3, requires=IS_INT_IN_RANGE(2, 7),
          label=T("Rychlá identifikace"), comment=T(
            "[DŮLEŽITÉ: později NEMĚNIT!] kolikamístné číslo používat pro rychlé hledání knihy z klávesnice? zvol podle velikosti knihovny: 2 - do počtu 50 výtisků, 3 - do 500, 4 - do 5000, 5 - do 50000, 6 - nad 50000")),
    Field('st_imp_bc', 'boolean', notnull=True, default=False,  # libstyle['bc'][0] = B
          label=T("Čarové kódy ?"), comment=T("označte, pokud knihovna používá vlastní čarové kódy")),
    Field('st_imp_bc2', 'boolean', notnull=True, default=True,  # libstyle['bc'][1] = +
          label=T("Inkremetovat čar.kódy ?"), comment=T(
            "Ano: čarový kód více výtisků bude předvyplněn zvětšujícím se číslem; Ne: čar.kód 2+ výtisku doplníte ručně")),
    Field('st_imp_pl', 'boolean', notnull=True, default=False,  # libstyle['gr'][0] = P
          label=T("Umístění výtisku ?"),
          comment=T("označte, pokud chcete zapisovat, kde je výtisk umístěn (oddělení, místnost, regál, apod.)")),
    Field('st_imp_sg', 'boolean', notnull=True, default=False,  # libstyle['sg'][0] = G
          label=T("Signatura výtisku ?"),
          comment=T("označte, pokud používáte signatury a každý výtisk má mít unikátní")),
    Field('st_imp_sgsep', 'string', length=3, notnull=True, default='',  # libstyle['sgsep']
          label=T("Oddělovač v signatuře"),
          comment=T("unikátní signatura výtisku (je-li použita): znak(y) pro oddělení dodatku")),
    Field('st_imp_sgmod1', 'string', length=1, notnull=True, default='',  # libstyle['sg'][1]
          label=T("Signatura, 1.výtisk"),
          comment=T("unikátní signatura výtisku (je-li použita): přídavný znak 1.výtisku (např. prázdný, a, A, 1)")),
    Field('st_imp_sgmod2', 'string', length=1, notnull=True, default='b',  # libstyle['sg'][2]
          label=T("Signatura, 2.výtisk"),
          comment=T("unikátní signatura výtisku (je-li použita): přídavný znak 2.výtisku (např. a, b, B, 2)")),
    Field('st_imp_st', 'boolean', notnull=True, default=False,  # libstyle['gr'][1] = s
          label=T("Stat.dělení výtisků ?"), comment=T(
            "označte, pokud chcete pro účel statistiky rozdělovat výtisky (tip: i pro oddělení dosp/děts, pokud výtisky titulu mohou být přiděleny do různých oddělení)")),
    Field('st_tit_st', 'boolean', notnull=True, default=False,  # libstyle['gr'][2] = S
          label=T("Stat.dělení titulů ?"), comment=T("označte, pokud chcete pro účel statistiky rozdělovat tituly")),
    Field('imp_total', 'integer', readable=False, default=0,
          label=T("Počet v importu"), comment=T("počet publikací, které budou/byly celkově importovány")),
    Field('imp_proc', 'decimal(5,2)', readable=False, writable=False, default=100.0),  # import position in %
    Field('imp_done', 'integer', readable=False, default=0,
          label=T("Počet již importovaných"),
          comment=T("počet již importovaných publikací celkem (nových i existujících)")),  # imp_done cnt
    Field('imp_new', 'integer', readable=False, default=0,
          label=T("Počet nových"), comment=T("počet nových již importovaných publikací")),  # imp_new cnt
    Field('last_import', 'datetime', writable=False,
          label=T("Naposledy importováno"), comment=T("čas posledního importu z jiného systému")),
    '''

    form = SQLFORM(db.library, auth.library_id,
                   formstyle=formstyle_bootstrap3_compact_factory(),
                   submit_button=T("Uložit"))
    if form.process().accepted:
        __clear_libstyle()
        response.flash = T("Uloženo")
    return dict(form=form, important=important, section=section)


def __clear_libstyle():   # session.libstyle will be recreated when needed
    if 'libstyle' in session:
        del session.libstyle


@auth.requires_login()
def places():
    db.place.id.readable = False
    grid = SQLFORM.grid(db.place,
            searchable=False,
            showbuttontext=False,
            csv=False
            )
    return dict(grid=grid)

@auth.requires_login()
def stgri():
    db.stat_group.id.readable = False
    db.stat_group.tbl.readable = db.stat_group.tbl.writable = False
    db.stat_group.tbl.default = 'I'
    grid = SQLFORM.grid(db.stat_group,
            searchable=False,
            showbuttontext=False,
            csv=False
            )
    db.stat_group._common_filter = lambda query: (db.stat_group.library_id == auth.library_id) & (db.stat_group.tbl == 'I')
    return dict(grid=grid)

@auth.requires_login()
def stgrt():
    db.stat_group.id.readable = False
    db.stat_group.tbl.readable = db.stat_group.tbl.writable = False
    db.stat_group.tbl.default = 'T'
    grid = SQLFORM.grid(db.stat_group,
            searchable=False,
            showbuttontext=False,
            csv=False
            )
    db.stat_group._common_filter = lambda query: (db.stat_group.library_id == auth.library_id) & (db.stat_group.tbl == 'T')
    return dict(grid=grid)

@auth.requires_login()
def stgrr():
    db.stat_group.id.readable = False
    db.stat_group.tbl.readable = db.stat_group.tbl.writable = False
    db.stat_group.tbl.default = 'R'
    grid = SQLFORM.grid(db.stat_group,
            searchable=False,
            showbuttontext=False,
            csv=False
            )
    db.stat_group._common_filter = lambda query: (db.stat_group.library_id == auth.library_id) & (db.stat_group.tbl == 'R')
    return dict(grid=grid)

'''
@auth.requires_login()
def stgrb():
    db.stat_group.id.readable = False
    db.stat_group.tbl.readable = db.stat_group.tbl.writable = False
    db.stat_group.tbl.default = 'B'
    grid = SQLFORM.grid(db.stat_group,
            searchable=False,
            showbuttontext=False,
            csv=False
            )
    db.stat_group._common_filter = lambda query: (db.stat_group.library_id == auth.library_id) & (db.stat_group.tbl == 'B')
    return dict(grid=grid)
'''
