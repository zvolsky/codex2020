# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip current chromedriver into path from CHROME_PATH / [private/appconfig.ini:]splinter.chromedriver
# run the server which shell be tested
# run tests from url <app>/plugin_splinter/tests

# started test has file models/_tests.py which forces use of testing database from the testers ip
#   in case of broken test you have to remove models/_tests.py (to allow normal mode from testers ip)


from posixpath import join as urljoin

from plugin_mz import formstyle_bootstrap3_compact_factory
from plugin_splinter import TestStatus, get_tested_servers, TESTS_ARE_ON_MSG, TESTS_ARE_OFF_MSG, OLD_TESTS_MSG
from tests_splinter import TESTCLASSES


TESTS_TIMEOUT = 30000  # ~ 8 hours
try:
    TESTADMIN = myconf.take('splinter.testgroup')
except BaseException:
    TESTADMIN = 'admin'

@auth.requires_membership(TESTADMIN)
def testdb_on():
    if TestStatus().tests_on():
        return TESTS_ARE_ON_MSG
    else:
        return OLD_TESTS_MSG

@auth.requires_membership(TESTADMIN)
def testdb_off():
    TestStatus().tests_off()
    return TESTS_ARE_OFF_MSG

@auth.requires_membership(TESTADMIN)
def tests():
    tested_servers = get_tested_servers(myconf)
    if not tested_servers:
        return 'Define tested servers in [splinter] section of private/appconfig.ini: server1=, server2=,.. ; each server in format: url;adminuser;password'

    dynamic_flds = []
    server_comment = 'SERVERS'
    server_default = True
    for server_no, tested_server in enumerate(tested_servers):
        dynamic_flds.append(Field(tested_server['fldname'], 'boolean', label=tested_server['url'],
                                  comment=server_comment, default=server_default))
        server_comment = ''
        server_default = False

    dynamic_flds.append(Field('unlogged_all', 'boolean', label='TestUnloggedAll', comment='TESTS', default=True))
    dynamic_flds.append(Field('all_tests', 'boolean', label='all tests bellow (from tests_splinter.py)', comment='', default=True))
    for testClass in TESTCLASSES:
        dynamic_flds.append(Field('test_' + testClass, 'boolean', label=testClass, comment='', default=False))

    form = SQLFORM.factory(
        Field('scheduler', 'boolean', label='run in scheduler', comment='MODE', default=True),
        Field('chrome', 'boolean', label='chrome', comment='BROWSERS', default=True),
        Field('firefox', 'boolean', label='firefox', comment='** FF 47+ requires Selenium 3+', default=False),
        *dynamic_flds,
        formstyle=formstyle_bootstrap3_compact_factory()
        )
    if form.process().accepted:
        servers = []
        server_no = 1
        while True:
            fldname = 'server%s' % server_no
            server_do = form.vars.get(fldname)
            if server_do is None:  # no more servers configured
                break
            if server_do:
                for server in tested_servers:  # without building the index on fldname, because we have few servers only
                    if server['fldname'] == fldname:
                        servers.append(server)
                        break
            server_no += 1

        if servers:
            if form.vars.scheduler:
                scheduler.queue_task(run_tests,
                        pvars={'form_vars': form.vars, 'servers': servers},
                        timeout=TESTS_TIMEOUT)
            else:
                run_tests(form.vars, servers)  # debug

    try:
        urit = myconf.take('db.urit') and ''  # do not show because contains a password
    except BaseException:
        urit = ' -- Not configured. Tests will fail.'
    return dict(form=form, urit=urit)
