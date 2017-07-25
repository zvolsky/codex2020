# -*- coding: utf-8 -*-

import urllib2

def api():
    if request.args[0] == 'zonky':
        url = 'https://api.zonky.cz/loans/marketplace?rating__eq=%s' % request.args[1]
        urllib_request = urllib2.Request(url)
        urllib_request.add_header('X-Page', '0')
        urllib_request.add_header('X-Size', '0')

    if urllib_request:
        response.headers = {'Access-Control-Allow-Origin': '*'}
        return urllib2.urlopen(urllib_request).read()
    else:
        raise HTTP(403)
