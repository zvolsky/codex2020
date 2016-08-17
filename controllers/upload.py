# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
from urllib import quote

from dal_utils import get_library
from c2_config import get_contact

from plugin_mz import utc_to_local


@auth.requires_login()
def main():
    email = None
    if auth.user.librarian:
        library = get_library()
        if library.imp_proc < 100.0:
            redirect(URL('running'))

        system = library.imp_system
        if system:
            redirect(URL(quote(system, safe='')))
        email = get_contact(myconf, 'imports')
    return dict(email=email)

@auth.requires_login()
def running():
    if not auth.user.librarian:
        redirect(URL('default', 'index'))
    library = get_library()
    if library.imp_proc >= 100.0:
        iinfo = db(db.import_run).select(orderby=~db.import_run.finished, limitby=(0, 1)).first()
        if iinfo and iinfo.finished:
            session.flash = T("Import katalogu byl dokončen v %s." % utc_to_local(iinfo.finished).strftime('%H:%M'))
        redirect(URL('default', 'index'))
    iinfo = db(db.import_run.finished==None).select().first()
    started = utc_to_local(iinfo.started) if iinfo else None
    return dict(started=started, imp_proc=library.imp_proc)

@auth.requires_login()
def codex():
    uploadfolder = os.path.join('applications', request.application, 'uploads', 'codex', get_library().slug)
    form = SQLFORM.factory(
        Field('knihy_d', 'upload', uploadfolder=uploadfolder, label='Knihy.dbf'),
        Field('knihy_m', 'upload', uploadfolder=uploadfolder, label='Knihy.fpt'),
    )
    if form.process().accepted:
        #from dbfread import DBF
        #for record in DBF(os.path.join(uploadfolder, form.vars.knihy_d), load=True)[:5]:
        #    print record
        import dbf
    return dict(form=form)
