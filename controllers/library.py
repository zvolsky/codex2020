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
