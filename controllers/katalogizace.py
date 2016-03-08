# -*- coding: utf-8 -*-

def publikace():
    link('js/codex2020/katalogizace/publikace')
    form = SQLFORM(db.publikace)
    return dict(form=form)

# ajax
def hledej_appendkey():
    return request.vars.appendkey
