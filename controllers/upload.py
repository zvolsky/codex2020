# -*- coding: utf-8 -*-

"""
    catalogue import
"""

import os
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

    link('js/fine-uploader/fine-uploader-gallery.min.css')
    link('js/fine-uploader/jquery.fine-uploader.min.js')
    return dict()

'''
    <link href="fine-uploader/fine-uploader-gallery.min.css" rel="stylesheet">
    <script src="fine-uploader/fine-uploader.min.js""></script>
'''

def ccc():
    #link('js/fine-uploader/fine-uploader-gallery.min.css')
    #link('js/fine-uploader/jquery.fine-uploader.min.js')
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script
          src="https://code.jquery.com/jquery-1.12.4.min.js"
          integrity="sha256-ZosEbRLbNQzLpnKIkEdrPv7lOy9C27hHQ+Xp8a4MxAQ="
          crossorigin="anonymous">
    </script>
    <link href="/codex2020/static/js/fine-uploader/fine-uploader-gallery.min.css" rel="stylesheet">
    <script src="/codex2020/static/js/fine-uploader/jquery.fine-uploader.min.js""></script>
    <script type="text/template" id="qq-template">
        <div class="qq-uploader-selector qq-uploader qq-gallery" qq-drop-area-text="Drop files here">
            <div class="qq-total-progress-bar-container-selector qq-total-progress-bar-container">
                <div role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" class="qq-total-progress-bar-selector qq-progress-bar qq-total-progress-bar"></div>
            </div>
            <div class="qq-upload-drop-area-selector qq-upload-drop-area" qq-hide-dropzone>
                <span class="qq-upload-drop-area-text-selector"></span>
            </div>
            <div class="qq-upload-button-selector qq-upload-button">
                <div>Upload a file</div>
            </div>
            <span class="qq-drop-processing-selector qq-drop-processing">
                <span>Processing dropped files...</span>
                <span class="qq-drop-processing-spinner-selector qq-drop-processing-spinner"></span>
            </span>
            <ul class="qq-upload-list-selector qq-upload-list" role="region" aria-live="polite" aria-relevant="additions removals">
                <li>
                    <span role="status" class="qq-upload-status-text-selector qq-upload-status-text"></span>
                    <div class="qq-progress-bar-container-selector qq-progress-bar-container">
                        <div role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" class="qq-progress-bar-selector qq-progress-bar"></div>
                    </div>
                    <span class="qq-upload-spinner-selector qq-upload-spinner"></span>
                    <div class="qq-thumbnail-wrapper">
                        <img class="qq-thumbnail-selector" qq-max-size="120" qq-server-scale>
                    </div>
                    <button type="button" class="qq-upload-cancel-selector qq-upload-cancel">X</button>
                    <button type="button" class="qq-upload-retry-selector qq-upload-retry">
                        <span class="qq-btn qq-retry-icon" aria-label="Retry"></span>
                        Retry
                    </button>

                    <div class="qq-file-info">
                        <div class="qq-file-name">
                            <span class="qq-upload-file-selector qq-upload-file"></span>
                            <span class="qq-edit-filename-icon-selector qq-btn qq-edit-filename-icon" aria-label="Edit filename"></span>
                        </div>
                        <input class="qq-edit-filename-selector qq-edit-filename" tabindex="0" type="text">
                        <span class="qq-upload-size-selector qq-upload-size"></span>
                        <button type="button" class="qq-btn qq-upload-delete-selector qq-upload-delete">
                            <span class="qq-btn qq-delete-icon" aria-label="Delete"></span>
                        </button>
                        <button type="button" class="qq-btn qq-upload-pause-selector qq-upload-pause">
                            <span class="qq-btn qq-pause-icon" aria-label="Pause"></span>
                        </button>
                        <button type="button" class="qq-btn qq-upload-continue-selector qq-upload-continue">
                            <span class="qq-btn qq-continue-icon" aria-label="Continue"></span>
                        </button>
                    </div>
                </li>
            </ul>

            <dialog class="qq-alert-dialog-selector">
                <div class="qq-dialog-message-selector"></div>
                <div class="qq-dialog-buttons">
                    <button type="button" class="qq-cancel-button-selector">Close</button>
                </div>
            </dialog>

            <dialog class="qq-confirm-dialog-selector">
                <div class="qq-dialog-message-selector"></div>
                <div class="qq-dialog-buttons">
                    <button type="button" class="qq-cancel-button-selector">No</button>
                    <button type="button" class="qq-ok-button-selector">Yes</button>
                </div>
            </dialog>

            <dialog class="qq-prompt-dialog-selector">
                <div class="qq-dialog-message-selector"></div>
                <input type="text">
                <div class="qq-dialog-buttons">
                    <button type="button" class="qq-cancel-button-selector">Cancel</button>
                    <button type="button" class="qq-ok-button-selector">Ok</button>
                </div>
            </dialog>
        </div>
    </script>

    <title>Fine Uploader Gallery UI</title>
</head>
<body>
    <div id="uploader"></div>
    <script>
        // Some options to pass to the uploader are discussed on the next page
        var uploader = new qq.FineUploader({
            element: document.getElementById("uploader"),
            request: {
                endpoint: "bbb"
            },
        })
    </script>
</body>
</html>    '''

def bbb():
    import simplejson
    # request.vars.keys() : ['qqtotalfilesize', 'qqfilename', 'qquuid', 'qqfile']  qqfile == FieldStorage
    from pdb import set_trace; set_trace()
    return simplejson.dumps({'success': True})

'''
var manualUploader = new qq.FineUploader({
        element: document.getElementById("fineuploader-container"),
        request: {
            endpoint: "/vendor/fineuploader/php-traditional-server/endpoint.php"
        },
        deleteFile: {
            enabled: true,
            endpoint: "/vendor/fineuploader/php-traditional-server/endpoint.php"
        },
        chunking: {
            enabled: true,
            concurrent: {
                enabled: true
            },
            success: {
                endpoint: "/vendor/fineuploader/php-traditional-server/endpoint.php?done"
            }
        },
        resume: {
            enabled: true
        },
        retry: {
            enableAuto: true,
            showButton: true
        }
    });
'''
