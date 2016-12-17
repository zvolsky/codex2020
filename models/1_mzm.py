# -*- coding: utf-8 -*-

import datetime

from plugin_mz import link

if request.is_local:
    from gluon.custom_import import track_changes
    track_changes(True)    # auto-reload modules
elif request.is_https:
    session.secure()

link('css/mz-bootstrap3.css')
