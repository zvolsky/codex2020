# -*- coding: utf-8 -*-

# mz support for Web2py application
# version 0.2 (current; the older versions can probably be rewritten by this one)
# TODO: change to git sub-repo


import datetime
import time

from gluon import current

from gluon.html import URL, SPAN, DIV, CAT, UL, TEXTAREA, INPUT, LABEL, SELECT, P
from gluon.sqlhtml import add_class


admin_mail = 'admin@' + '.'.join(current.request.env.http_host.rsplit('.')[-2:])


def link(src):
    if src in ('alertify', 'alertifyjs'):
        link('js/alertifyjs/alertify.min.js')
        link('js/alertifyjs/css/alertify.min.css')
        link('js/alertifyjs/css/themes/default.min.css')
    elif src in ('fine-uploader', 'fineuploader'):
        link('js/fine-uploader/fine-uploader-gallery.min.css')
        link('js/fine-uploader/jquery.fine-uploader.min.js')

    elif '://' in src:
        current.response.files.append(src)
    else:
        current.response.files.append(URL('static', src))


def force_download(filename, content, mime_type=None):
    """download sestavené stránky
    explicitní Content-Type může být string/unicode nebo iterable (list, tuple)
        to je preferovaný způsob
    implicitně se použije nějaká oblíbená sada PHP vývojářů
        to je nevhodný způsob, ale snad funkční, pokud se prohlížeč vzpěčuje
    """
    if 'attachment' in current.request.vars:
        current.response.headers['Content-Disposition'] = 'attachment; filename="%s"' % filename
        if mime_type is None:
            current.response.headers['Content-Type'] = 'application/force-download'
            current.response.headers['Content-Type'] = 'application/octet-stream'
            current.response.headers['Content-Type'] = 'application/download'
        elif isinstance(mime_type, basestring):
            current.response.headers['Content-Type'] = mime_type
        else:
            for mt in mime_type:
                current.response.headers['Content-Type'] = mt
        current.response.headers['Content-Length'] = '%s' % len(content)
    return content

def formstyle_bootstrap3_compact_factory(col_label_size=2, col_help_size=6,
                                         input_class='input-sm', control_label='control-label-sm'):
    """formstyle=formstyle_bootstrap3_compact_factory()
    TODO: control-label-sm není defnovaná (jako control-label, ale bez posunu dolů
    """
    def _inner(form, fields):
        form.add_class('form-horizontal')
        label_col_class = "col-sm-%d" % col_label_size
        col_class = "col-sm-%d" % (12 - col_label_size - col_help_size)
        col_class_rest = "col-sm-%d" % (12 - col_label_size)
        offset_class = "col-sm-offset-%d" % col_label_size
        help_class = "col-sm-%d" % col_help_size
        parent = CAT()
        for id, label, controls, help in fields:
            # wrappers
            _help = DIV(SPAN(help, _class='help-block'), _class="%s" % (help_class))
            # embed _help into _controls
            _controls = DIV(controls, _class="%s" % (col_class))
            if isinstance(controls, INPUT):
                if controls['_type'] == 'submit':
                    controls.add_class('btn btn-primary')
                    _controls = DIV(DIV(controls, _class="btn-group-sm"), _class="%s %s" % (col_class_rest, offset_class))
                if controls['_type'] == 'button':
                    controls.add_class('btn btn-default')
                elif controls['_type'] == 'file':
                    controls.add_class('input-file')
                    controls.add_class(input_class)
                elif controls['_type'] in ('text', 'password'):
                    controls.add_class('form-control')
                    controls.add_class(input_class)
                elif controls['_type'] == 'checkbox':
                    label['_for'] = None
                    label.insert(0, controls)
                    label.insert(1, ' ')
                    _controls = DIV(DIV(label, _class="checkbox"),
                                    _class="%s %s" % (offset_class, col_class))
                    label = ''
                elif isinstance(controls, (SELECT, TEXTAREA)):
                    controls.add_class('form-control')
                    controls.add_class(input_class)

            elif isinstance(controls, SPAN):
                _controls = P(controls.components,
                              _class="form-control-static %s" % col_class)
            elif isinstance(controls, UL):
                for e in controls.elements("input"):
                    e.add_class('form-control')

            else:
                _controls = DIV(controls, _class="small %s" % (col_class))

            if isinstance(label, LABEL):
                label['_class'] = add_class(label.get('_class'), '%s %s' % (control_label, label_col_class))

            parent.append(DIV(label, _controls, _help, _class='row', _id=id))
        return DIV(parent, _class='form-group')
    return _inner

def utc_to_local(utc_datetime):
    now_timestamp = time.time()
    offset = datetime.datetime.fromtimestamp(now_timestamp) - datetime.datetime.utcfromtimestamp(now_timestamp)
    return utc_datetime + offset

def lpdb(txt):
    import os
    if isinstance(txt, unicode):
        txt = txt.encode('utf8')
    with open(os.path.join(os.path.expanduser("~"), 'lpdb'), 'a') as f:
        f.write(txt + '\n')
