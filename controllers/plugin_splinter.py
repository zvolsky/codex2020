# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip (into path from CHROME_PATH) current chromedriver
# run the server which shell be tested

from plugin_splinter import run_for_server


URLLOCAL = 'http://localhost:8080'


def tests():
    production = myconf.take('splinter.production')
    form = SQLFORM.factory(
        Field('chrome', 'boolean', label='Browser', comment='chrome', default=True),
        Field('firefox', 'boolean', label='', comment='firefox', default=False),
        Field('develop', 'boolean', label='Server', comment='local/develop', default=True),
        Field('production', 'boolean', default=False, writable=production, label='',
              comment=production if production else '(define url: splinter.production in private/appconfig.ini)'),
        Field('all_tests', 'boolean', label='Tests', comment='local/develop', default=True),
    )
    if form.process().accepted:
        if form.vars.develop:
            run_for_server(URLLOCAL, form.vars)
        if form.vars.chrome:
            run_for_server(production, form.vars)
    return dict(form=form)
