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
    '''
    form = SQLFORM.factory(
        Field('knihy_d', 'upload', uploadfolder=uploadfolder, label='Knihy.dbf'),
        Field('knihy_m', 'upload', uploadfolder=uploadfolder, label='Knihy.fpt'),
    )
    '''
    if request.vars:
        needed = {'autori.dbf', 'k_autori.dbf', 'dodavat.dbf', 'dodavat.fpt', 'dt.dbf', 'dt.fpt', 'k_dt.dbf', 'klsl.dbf', 'k_klsl.dbf',
                  'knihy.dbf', 'knihy.fpt', 'vytisk.dbf', 'vytisk.fpt'}
        handle = needed.copy()

        for f in request.vars.codex:
            fn = f.filename.lower()
            if fn in needed:
                needed.remove(fn)
        if needed:
            session.flash = "Nejsou označeny soubory %s. Zkus to ještě jednou." % str([fn for fn in needed])
            redirect(URL())

        uploadfolder = os.path.join(request.folder, 'uploads', 'codex', get_library().slug)
        if not os.path.isdir(uploadfolder):
            os.makedirs(uploadfolder)

        for f in request.vars.codex:
            fn = f.filename.lower()
            if fn in handle:
                import pdb;pdb.set_trace()

                content = f.read_binary()
                with open(os.path.join(uploadfolder, fn), 'w') as fw:
                    fw.write(content)

        redirect(URL())
    return dict()
