# -*- coding: utf-8 -*-

from plugin_mz import formstyle_bootstrap3_compact_factory
# from dal_common import get_my_libraries   # in choose_library()

@auth.requires_login()
def choose_library():
    """
        request.args(0): missing: Show, 'all': ShowAll, '<id>': Set
    """
    from dal_common import get_my_libraries

    active = None    # id of the selected library
    accessible = []  # or other libraries accessible for this user, (id, name)
    curr_lib = session.library_id
    spec_request = request.args(0)
    allowed_all = auth.has_membership('admin')
    show_all = allowed_all and spec_request == 'all'
    if allowed_all or auth.user.library_id:
        rows = db(db.library).select(db.library.id, db.library.library, orderby=db.library.library)
        #                                       Admin-Show Admin-ShowAll Admin-Set User-Show User-Set
        # allowed_all                           True        True        True        False       False
        # show_all                              False       True        False       False       False
        # not show_all                          True        False       True        True        True
        # spec_request                          False       True        True        False       True
        # not (allowed_all and spec_request)    True        False       False       True        True
        # if.... (ie. apply filter)             True        False       False       True        True
        my_libraries = get_my_libraries()
        if not show_all and not (allowed_all and spec_request):
            rows = rows.find(lambda r: r.id in my_libraries)
        if spec_request and spec_request != 'all':  # Set the library
            for row in rows:
                if str(row.id) == spec_request:
                    session.library_id = row.id
                    redirect(URL('default', 'index'))  # if Set (and <id> is legal) then it will stop here
                    break
        for row in rows:
            if row.id == curr_lib:
                active = row.library
            else:
                accessible.append((row.id, row.library))
        if not active and curr_lib:  # this shouldn't be: improper library was assigned
            del session.library_id
    return dict(active=active, accessible=accessible, show_all=show_all)


@auth.requires_login()
def new():
    """will create library for the new librarian"""
    for sfld in db.library.fields:
        fld = db.library[sfld]
        fld.writable = fld.readable = False
    db.library.library.writable = db.library.library.readable = True
    db.library.ltype.writable = db.library.ltype.readable = True

    form = SQLFORM(db.library,
                   formstyle=formstyle_bootstrap3_compact_factory(),
                   submit_button=T("Vytvořit knihovnu"))
    if not auth.library_id:
        form.vars.library = T("zkušební") + ' ' + auth.user.username
    if form.process().accepted:
        __clear_libstyle()
        auth_lib_id = db.auth_lib.insert(auth_user_id=auth.user_id, library_id=form.vars.id)
        now = datetime.datetime.now()
        db.lib_rights.insert(auth_lib_id=auth_lib_id, allowed='W', given=now)
        db.lib_rights.insert(auth_lib_id=auth_lib_id, allowed='A', given=now)
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
