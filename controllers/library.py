# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory


@auth.requires_login()
def new():
    """will create library for the new librarian"""
    form = SQLFORM(db.library,
                   formstyle=formstyle_bootstrap3_compact_factory(),
                   submit_button=T("Pokračovat ke katalogizaci"))
    if form.process().accepted:
        __clear_libstyle()
        auth.user.library_id.insert(0, form.vars.id)
        db.auth_user[auth.user_id] = dict(library_id=auth.user.library_id)
        auth.library_id = form.vars.id
        redirect(URL('catalogue', 'find'))
    return dict(form=form)

@auth.requires_login()
def library():
    """edit info about librarian's library"""
    if not auth.library_id:
        redirect(URL('default', 'index'))
    db.library.id.readable = False
    form = SQLFORM(db.library, auth.library_id, formstyle=formstyle_bootstrap3_compact_factory())
    if form.process().accepted:
        __clear_libstyle()
        redirect(URL('default', 'index'))
    return dict(form=form)

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
