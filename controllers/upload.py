# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
from urllib import quote

from dal_import import clear_before_import, cancel_import
from dal_utils import get_library
from c2_config import get_contact

from plugin_mz import utc_to_local

if False:  # for IDE only, need web2py/__init__.py
    from web2py.applications.codex2020.models.scheduler import do_import

    from web2py.applications.codex2020.modules.dal_import import clear_before_import, cancel_import
    from web2py.applications.codex2020.modules.dal_utils import get_library
    from web2py.applications.codex2020.modules.c2_config import get_contact
    from web2py.applications.codex2020.modules.plugin_mz import utc_to_local


MAX_FILE_SIZE = 67108864   # upload max 64 MB single FoxPro file


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
    msg_fin = None
    iinfo = db(db.import_run).select(orderby=~db.import_run.started, limitby=(0, 1)).first()
    library = get_library()
    if library.imp_proc >= 100.0:
        if iinfo and iinfo.finished:
            msg_fin = T("Import katalogu byl dokončen v %s." % utc_to_local(iinfo.finished).strftime('%H:%M'))
    counts = db(db.library.id == auth.library_id).select(db.library.imp_total, db.library.imp_proc, db.library.imp_done, db.library.imp_new).first()
    started = utc_to_local(iinfo.started) if iinfo else None

    can_stop = False
    if msg_fin is None:
        if session.imp_done == counts.imp_done:
            can_stop = True
        else:
            session.imp_done = counts.imp_done
    return dict(started=started, imp_proc=library.imp_proc, counts=counts, msg_fin=msg_fin, can_stop=can_stop)


@auth.requires_login()
def cancel():
    cancel_import()
    redirect(URL('default', 'index'))


@auth.requires_login()
def codex():
    if not auth.user.librarian or not auth.library_id:
        redirect(URL('default', 'index'))

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
            # fn = filter(lambda s: s.replace('_', 'a').isalnum(), fn)  # for security disallow non-alphanum characters // no need to do it, because we will choose some names only
            if fn in handle:
                with open(os.path.join(uploadfolder, fn), 'w') as fw:
                    content = f.value
                    if len(content) > MAX_FILE_SIZE:
                        break
                    fw.write(content)

        clear_before_import()
        #do_import('imp_codex', auth.library_id, src_folder=uploadfolder, full=True)  # debug
        #redirect(URL('default', 'index'))
        scheduler.queue_task(do_import,
                pvars={'imp_func': 'imp_codex', 'library_id': auth.library_id, 'src_folder': uploadfolder, 'full': True},
                timeout=7200)
        redirect(URL('running'))
    return dict()
