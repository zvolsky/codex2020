# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
from urllib import quote

from dal_idx import idx_schedule
from dal_import import clear_before_import, cancel_import
from dal_utils import get_library
from c2_config import get_contact

from plugin_mz import link, utc_to_local

if False:  # for IDE only, need web2py/__init__.py
    from web2py.applications.codex2020.models.scheduler import do_import

    from web2py.applications.codex2020.modules.dal_idx import idx_schedule
    from web2py.applications.codex2020.modules.dal_import import clear_before_import, cancel_import
    from web2py.applications.codex2020.modules.dal_utils import get_library
    from web2py.applications.codex2020.modules.c2_config import get_contact
    from web2py.applications.codex2020.modules.plugin_mz import link, utc_to_local


MAX_FILE_SIZE = 67108864   # upload max 64 MB single FoxPro file
UPLOAD_ROOT = os.path.join(request.folder, 'imports', str(auth.library_id))
UPLOAD_RELATIVE = 'src'


@auth.requires_login()
def main():
    email = None
    if auth.user.librarian:
        library = get_library()
        if library is None:
            session.flash = T("Nemáš nastavenou žádnou knihovnu, kterou právě spravuješ. Je třeba provést Nastavení.")
            redirect(URL('default', 'index'))
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
    library = get_library()
    iinfo = db.import_run[session.import_run_id]
    if library.imp_proc >= 100.0:
        msg_fin = (True, T("Import katalogu byl dokončen v %s.") % utc_to_local(library.last_import).strftime('%H:%M'))
    else:
        if iinfo and iinfo.scheduler_task_id:
            status = scheduler.task_status(iinfo.scheduler_task_id)
            if status.status == 'FAILED':
                msg_fin = (False, T("Import katalogu selhal. Prosím, kontaktujte podporu."))
                cancel_import()
    counts = db(db.library.id == auth.library_id).select(db.library.imp_total, db.library.imp_proc, db.library.imp_done, db.library.imp_new).first()
    counts.imp_total = counts.imp_total or 0
    counts.imp_done = counts.imp_done or 0
    counts.imp_new = counts.imp_new or 0

    started = None
    if iinfo:
        started = utc_to_local(iinfo.started)

    can_stop = False
    if msg_fin is None:
        if session.imp_done == counts.imp_done:  # count has not changed from previous attempt; it hangs??
            can_stop = True
        else:
            session.imp_done = counts.imp_done
    return dict(started=started, imp_proc=library.imp_proc, counts=counts, msg_fin=msg_fin, can_stop=can_stop)


@auth.requires_login()
def cancel():
    cancel_import()
    redirect(URL('default', 'index'))


@auth.requires_login()
def import_uploaded():
    """
        args[0] - required import function; example: 'imp_codex' for codex import
    Returns:

    """
    if len(request.args) != 1:
        raise HTTP(404)

    session.import_run_id = clear_before_import()

    uploadfolder = os.path.join(UPLOAD_ROOT, UPLOAD_RELATIVE)
    if DEBUG_SCHEDULER:
        do_import(request.args[0], auth.library_id, src_folder=uploadfolder, full=True)  # debug
        redirect_url = URL('default', 'index')
    else:
        ref = scheduler.queue_task(do_import,
                pvars={'imp_func': request.args[0], 'library_id': auth.library_id, 'src_folder': uploadfolder, 'full': True},
                timeout=7200, group_name='slow')
        db.import_run[session.import_run_id] = {'scheduler_task_id': ref.id}
        idx_schedule()
        redirect_url = URL('running')

    # TODO: to remove, replaced with sysadmin/start_idx and scheduler
    #if DEBUG_SCHEDULER:
    #    idx()
    #else:
    #    scheduler.queue_task(idx, pvars={}, timeout=100)

    redirect(redirect_url)


@auth.requires_login()
def codex():
    if not auth.user.librarian or not auth.library_id:
        redirect(URL('default', 'index'))

    def sure_exists_and_empty(subfolder):
        folder = os.path.join(UPLOAD_ROOT, subfolder)
        if os.path.isdir(folder):
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        else:
            os.makedirs(folder)

    # jen když neběží import !! při běžícím nutno redirect()
    sure_exists_and_empty('tmp')
    sure_exists_and_empty(UPLOAD_RELATIVE)

    link('fine-uploader')
    link('alertifyjs')
    upload_filenames = ['autori.dbf', 'k_autori.dbf', 'dodavat.dbf', 'dodavat.fpt', 'dt.dbf', 'dt.fpt', 'k_dt.dbf', 'klsl.dbf', 'k_klsl.dbf',
                  'knihy.dbf', 'knihy.fpt', 'vytisk.dbf', 'vytisk.fpt']   # as lower!
    session.upload_filenames = upload_filenames
    session.upload_win = True
    return dict(upload_filenames=upload_filenames)

'''to be removed
def odpad():
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

        if DEBUG_SCHEDULER:
            do_import('imp_codex', auth.library_id, src_folder=uploadfolder, full=True)  # debug
            redirect_url = URL('default', 'index')
        else:
            scheduler.queue_task(do_import,
                    pvars={'imp_func': 'imp_codex', 'library_id': auth.library_id, 'src_folder': uploadfolder, 'full': True},
                    timeout=7200)
            redirect_url = URL('running')

        if DEBUG_SCHEDULER:
            idx()
        else:
            scheduler.queue_task(idx, pvars={}, timeout=100)

        redirect(redirect_url)

    return {}

@auth.requires_login()
def ccc():
    ROOT_IMPORT = os.path.join(request.folder, 'imports')

    def sure_exists_and_empty(subfolder):
        folder = os.path.join(ROOT_IMPORT, str(auth.user_id), subfolder)
        if os.path.isdir(folder):
            for the_file in os.listdir(folder):
                file_path = os.path.join(folder, the_file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        else:
            os.makedirs(folder)

    # jen když neběží import !! při běžícím nutno redirect()
    sure_exists_and_empty('tmp')
    sure_exists_and_empty('src')

    link('fine-uploader')
    link('alertifyjs')
    session.upload_filenames = ['knihy.dbf', 'knihy.fpt', 'knihy.cdx']
    # TODO: validovat na úrovni JavaScriptu pomocí .getUploads() /při .autoUpload = false/
    session.upload_win = True
    return {}
'''

'''
bez chunku:
nginx.conf: proxy_read_timeout 1200;
Apache equivalent is: ProxyTimeout seconds (defaults to 300), and the Gunicorn equivalent is: -t seconds (defaults to 30 !!).
'''

'''
https://github.com/FineUploader/server-examples/blob/master/python/flask-fine-uploader/app.py
'''
