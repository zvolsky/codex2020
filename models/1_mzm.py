# -*- coding: utf-8 -*-

import datetime

from mzm import accept, link
site_static = '../../../site-static/'
link(site_static + 'js/mzj', site_static + 'css/mzc')

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
if request.is_local:
    from gluon.custom_import import track_changes
    track_changes(True)    # auto-reload modules
#else:
#    request.requires_https()