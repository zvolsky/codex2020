# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip (into path from CHROME_PATH) current chromedriver
# run the server which shell be tested

import urlparse

from plugin_splinter import run_for_server
from tests_splinter import TESTCLASSES

from plugin_mz import formstyle_bootstrap3_compact_factory


URLLOCAL = 'http://localhost:8000'


def tests():
    testClassesFlds = []
    for testClass in TESTCLASSES:
        testClassesFlds.append(Field('test_' + testClass, 'boolean', label=testClass, comment='', default=False))

    production = myconf.take('splinter.production')
    form = SQLFORM.factory(
        Field('chrome', 'boolean', label='chrome', comment='Browser', default=True),
        Field('firefox', 'boolean', label='firefox', comment='** FF 47+ requires Selenium 3+', default=False),
        Field('develop', 'boolean', label='local/develop', comment='Server', default=True),
        Field('production', 'boolean', default=False, writable=production,
              label=production if production else '(define url: splinter.production in private/appconfig.ini)',
              comment=''),
        Field('all_tests', 'boolean', label='all', comment='Tests', default=True),
        *testClassesFlds,
        formstyle=formstyle_bootstrap3_compact_factory()
        )
    if form.process().accepted:
        if form.vars.develop:
            run_for_server(urlparse.urljoin(URLLOCAL, request.application), form.vars, myconf)
        if form.vars.production:
            run_for_server(production, form.vars, myconf)
    return dict(form=form)
