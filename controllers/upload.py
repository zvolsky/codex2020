# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
import simplejson
from urllib import quote

from dal_import import clear_before_import, cancel_import
from dal_utils import get_library
from c2_config import get_contact

from plugin_mz import link, utc_to_local

if False:  # for IDE only, need web2py/__init__.py
    from web2py.applications.codex2020.models.scheduler import do_import

    from web2py.applications.codex2020.modules.dal_import import clear_before_import, cancel_import
    from web2py.applications.codex2020.modules.dal_utils import get_library
    from web2py.applications.codex2020.modules.c2_config import get_contact
    from web2py.applications.codex2020.modules.plugin_mz import link, utc_to_local


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
            msg_fin = T("Import katalogu byl dokončen v %s.") % utc_to_local(iinfo.finished).strftime('%H:%M')
    counts = db(db.library.id == auth.library_id).select(db.library.imp_total, db.library.imp_proc, db.library.imp_done, db.library.imp_new).first()
    counts.imp_total = counts.imp_total or 0
    counts.imp_done = counts.imp_done or 0
    counts.imp_new = counts.imp_new or 0
    started = utc_to_local(iinfo.started) if iinfo else None

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
        if debug_scheduler:
            do_import('imp_codex', auth.library_id, src_folder=uploadfolder, full=True)  # debug
            redirect_url = URL('default', 'index')
        else:
            scheduler.queue_task(do_import,
                    pvars={'imp_func': 'imp_codex', 'library_id': auth.library_id, 'src_folder': uploadfolder, 'full': True},
                    timeout=7200)
            redirect_url = URL('running')

        if debug_scheduler:
            idx()
        else:
            scheduler.queue_task(idx, pvars={}, timeout=100)

        #from time import sleep
        #sleep(1)
        #scheduler.queue_task(idx, pvars={}, timeout=100)

        redirect(redirect_url)

    link('fine-uploader')
    link('alertifyjs')
    return {}

@auth.requires_login()
def ccc():
    link('fine-uploader')
    link('alertifyjs')
    return {}

# ajax
@auth.requires_login()
def uploader_request():
    # request.vars.keys() : ['qqtotalfilesize', 'qqfilename', 'qquuid', 'qqfile']  qqfile == FieldStorage
    # klíče se mohou měnit - viz Django example
    content = request.vars.qqfile.file.read()
    print 20*'-', request.vars.qqfilename, request.vars.qqpartindex, '/', request.vars.qqtotalparts, 30*'-'
    return simplejson.dumps({'success': True})

# ajax
@auth.requires_login()
def uploader_finished():
    print 30*'-', request.vars.qqfilename, 'finished', 30*'-'
    return simplejson.dumps({'success': True})

# ajax
@auth.requires_login()
def uploader_all_completed():
    print 50*'*'
    return simplejson.dumps({'success': True, 'msg': 'finished'})

# ajax
@auth.requires_login()
def uploader_auto_retry():
    return simplejson.dumps({'success': True})

# ajax
@auth.requires_login()
def uploader_manual_retry():
    return simplejson.dumps({'success': True})

'''
bez chunku:
nginx.conf: proxy_read_timeout 1200;
Apache equivalent is: ProxyTimeout seconds (defaults to 300), and the Gunicorn equivalent is: -t seconds (defaults to 30 !!).
'''

'''
https://github.com/FineUploader/server-examples/blob/master/python/flask-fine-uploader/app.py
'''
