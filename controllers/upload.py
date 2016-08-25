# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
from urllib import quote

# delayed import inside func: from import_codex import imp_codex
from dal_utils import get_library
from c2_config import get_contact

from plugin_mz import utc_to_local

if False:  # for IDE only, need web2py/__init__.py
    from web2py.applications.codex2020.models.scheduler import do_import

    from web2py.applications.codex2020.modules.dal_utils import get_library
    from web2py.applications.codex2020.modules.c2_config import get_contact
    from web2py.applications.codex2020.modules.plugin_mz import utc_to_local


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
    if not auth.user.librarian or not auth.library_id:
        redirect(URL('default', 'index'))

    # delayed import
    from import_codex import imp_codex
    if False:
        from web2py.applications.codex2020.modules.import_codex import imp_codex

    if request.vars.codex:
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
                with open(os.path.join(uploadfolder, fn), 'w') as fw:
                    fw.write(f.value)

        do_import(imp_codex, auth.library_id, src_folder=uploadfolder, full=True)  # debug
        redirect(URL('default', 'index'))
        #scheduler.queue_task(do_import,
        #        pvars={'imp_func': imp_codex, 'library_id': auth.library_id, 'src_folder': uploadfolder, 'full': True},
        #        timeout=7200)
        #redirect(URL('running'))
    return dict()
