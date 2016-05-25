# -*- coding: utf-8 -*-

def readers():
    db.reader.id.readable = False
    grid = SQLFORM.smartgrid(db.reader,
            orderby={'reader': 'lastname'},
            showbuttontext=False
            )
    return dict(grid=grid)

def groups():
    db.rgroup.id.readable = False
    db.reader.id.readable = False
    grid = SQLFORM.smartgrid(db.rgroup,
            orderby={'rgroup': 'rgroup', 'reader': 'lastname'},
            showbuttontext=False
            )
    return dict(grid=grid)
