# -*- coding: utf-8 -*-

if request.client != 'x.x.x.x':
    when_cz = '' or 'asi za hodinu'  # 'v 15h'

    if request.controller == 'default' and request.function in ['ip', 'client']:
        raise HTTP(503, request.client)

    msg = T('Server je dočasně mimo provoz, zkuste se prosím vrátit %s.') % when_cz
    raise HTTP(503, msg)

response.flash = '0_out'
