# -*- coding: utf-8 -*-

from mzutils import slugify
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
    important = db(db.library.id == auth.library_id).select(
            db.library.imp_system, db.library.slug, db.library.library).first()
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
    elif section == 'publish':
        db.library.is_public.writable = db.library.is_public.readable = True
        db.library.slug.writable = db.library.slug.readable = True
        if not important.slug and important.library:
            db.library[auth.library_id] = slugify(important.library)
            db.commit()

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
