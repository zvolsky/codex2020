# -*- coding: utf-8 -*-

"""
    ajax calls for js fine-uploader

    upload can be limited for given filenames only;
        to achieve this set the list session.upload_filenames
        if users can be from Windows systems:
            - set: session.upload_win = True
            - set session.upload_filenames in lowercase
            (uploaded files will have lowercase names)
"""

import os
import simplejson


UPLOAD_ROOT = os.path.join(request.folder, 'imports', str(auth.library_id))
UPLOAD_RELATIVE = 'src'
ROOT_TMP = os.path.join(UPLOAD_ROOT, 'tmp')
ROOT_SRC = os.path.join(UPLOAD_ROOT, UPLOAD_RELATIVE)


# ajax
@auth.requires_login()
def uploader_request():
    # klíče request.vars - viz fine-uploader, Django example
    filename = __upload_filename(request.vars.qqfilename)
    if filename:
        content = request.vars.qqfile.file.read()
        with open(os.path.join(ROOT_TMP, '_%s_%s' % (request.vars.qqpartindex, filename)), 'wb') as f:
            f.write(content)
        print 20*'-', filename, request.vars.qqpartindex, '/', request.vars.qqtotalparts, 30*'-'
    return simplejson.dumps({'success': True})

# ajax
@auth.requires_login()
def uploader_finished():
    filename = __upload_filename(request.vars.qqfilename)  # WARNING: we cannot manipulate session.upload_filenames here (to see if all required are uploaded) with regard to concurrent accesses which can save session in same time
    if filename:
        with open(os.path.join(ROOT_SRC, filename), 'wb') as f:
            idx = 0
            while True:
                chunk = os.path.join(ROOT_TMP, '_%s_%s' % (idx, filename))
                if not os.path.exists(chunk):
                    break
                with open(chunk, 'rb') as ch:
                    f.write(ch.read())
                os.unlink(chunk)
                idx += 1
        print 30*'-', request.vars.qqfilename, 'finished', 30*'-'
    return simplejson.dumps({'success': True})

# ajax
@auth.requires_login()
def uploader_all_completed():
    if session.upload_filenames:
        '''
        we cannot remove completed files immediately in uploader_finished() from session.upload_filenames
            because concurrent ajax calls save session in unpredictable times
        '''
        missing = session.upload_filenames
        session.forget()
        uploaded = os.listdir(ROOT_SRC)
        for the_file in uploaded:
            if the_file in missing:
                missing.remove(the_file)
        if missing:
            return simplejson.dumps({'success': False, 'missing': ', '.join(missing)})
    return simplejson.dumps({'success': True, 'missing': ''})

'''
# ajax
@auth.requires_login()
def uploader_auto_retry():
    return simplejson.dumps({'success': True})

# ajax
@auth.requires_login()
def uploader_manual_retry():
    return simplejson.dumps({'success': True})
'''

def __upload_filename(filename):
    """
        returns None if we don't need this file (i.e. it is not listed in session.upload_filenames)
        otherwise returns the filename
            if session.upload_win in lowercase (session.upload_filenames must be in lowecase too!!)
            otherwise without a change (upload from Linux style systems)
    """
    if session.upload_win:
        filename = filename.lower()
    if session.upload_filenames is None or filename in session.upload_filenames:
        return filename
    return None

'''
https://github.com/FineUploader/server-examples/blob/master/python/flask-fine-uploader/app.py
'''
