# -*- coding: utf-8 -*-

import urllib2

def api():
    if request.args[0] == 'zonky':
        url = 'https://api.zonky.cz/loans/marketplace?rating__eq=%s' % request.args[1]
    return urllib2.urlopen(url).read()
