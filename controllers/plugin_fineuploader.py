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

ROOT = '/home/mirek/mz/web2py/applications/codex2020/imports/' + str(auth.user_id)
ROOT_TMP = os.path.join(ROOT, 'tmp')
ROOT_SRC = os.path.join(ROOT, 'src')
if not os.path.isdir(ROOT_TMP):
    os.makedirs(ROOT_TMP)
if not os.path.isdir(ROOT_SRC):
    os.makedirs(ROOT_SRC)

# ajax
@auth.requires_login()
def uploader_request():
    # request.vars.keys() : ['qqtotalfilesize', 'qqfilename', 'qquuid', 'qqfile']  qqfile == FieldStorage
    # klíče se mohou měnit - viz Django example
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
    filename = __upload_filename(request.vars.qqfilename)
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

'''
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

def __upload_filename(filename):
    """
        returns None if we don't need this file (i.e. it is not listed in session.upload_filenames)
        otherwise returns the filename
            if session.upload_win in lowercase (session.upload_filenames must be in lowecase too!!)
            otherwise without a change (upload from Linux style systems)
    """
    if session.upload_win:
        filename = lower(filename)
    if not session.upload_filenames or filename in session.upload_filenames:
        return filename
    return None

'''
https://github.com/FineUploader/server-examples/blob/master/python/flask-fine-uploader/app.py
'''
