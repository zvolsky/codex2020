# -*- coding: utf-8 -*-

import urllib2

def api():
    if request.args[0] == 'zonky':
        url = 'https://api.zonky.cz/loans/marketplace?rating__eq=%s' % request.args[1]
        request = urllib2.Request(url)
        request.add_header('X-Page', '0')
        request.add_header('X-Size', '30')

    if request:
        response.headers = {'Access-Control-Allow-Origin': '*'}
        return urllib2.urlopen(request).read()
    else:
        raise HTTP(403)
