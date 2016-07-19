# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip current chromedriver into path from CHROME_PATH / [private/appconfig.ini:]splinter.chromedriver
# run the server which shell be tested
# run tests from url <app>/plugin_splinter/tests


from posixpath import join as urljoin

from tests_splinter import TESTCLASSES

from plugin_mz import formstyle_bootstrap3_compact_factory

URLLOCAL = 'http://localhost:8000/'              # request.application will be auto-added
PRODUCTION = myconf.take('splinter.production')  # with or without application (without: if supressed in routes)


def tests():
    testClassesFlds = []
    for testClass in TESTCLASSES:
        testClassesFlds.append(Field('test_' + testClass, 'boolean', label=testClass, comment='', default=False))

    form = SQLFORM.factory(
        Field('chrome', 'boolean', label='chrome', comment='Browser', default=True),
        Field('firefox', 'boolean', label='firefox', comment='** FF 47+ requires Selenium 3+', default=False),
        Field('develop', 'boolean', label='local/develop', comment='Server', default=True),
        Field('production', 'boolean', default=False, writable=PRODUCTION,
              label=PRODUCTION if PRODUCTION else '(define url: splinter.production in private/appconfig.ini)',
              comment=''),
        Field('all_tests', 'boolean', label='all', comment='Tests', default=True),
        *testClassesFlds,
        formstyle=formstyle_bootstrap3_compact_factory()
        )
    if form.process().accepted:
        urls = []
        if form.vars.develop:
            urls.append(urljoin(URLLOCAL, request.application))
        if form.vars.production:
            urls.append(PRODUCTION)

        if urls:
            scheduler.queue_task(run_tests,
                    pvars={'form_vars': form.vars, 'urls': urls},
                    timeout=3600)
            #run_tests(form.vars, urls)  # debug
    return dict(form=form)
