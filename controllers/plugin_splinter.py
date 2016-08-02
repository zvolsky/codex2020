# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip current chromedriver into path from CHROME_PATH / [private/appconfig.ini:]splinter.chromedriver
# run the server which shell be tested
# run tests from url <app>/plugin_splinter/tests

# started test has file models/_tests.py which forces use of testing database from the testers ip
#   in case of broken test you have to remove models/_tests.py (to allow normal mode from testers ip)


import base64

from plugin_mz import formstyle_bootstrap3_compact_factory
from plugin_splinter import (TestStatus, get_tested_servers, TESTS_ARE_ON_MSG, TESTS_ARE_OFF_MSG, OLD_TESTS_MSG,
                            TEST_PWD)
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

    dynamic_flds.append(Field('unlogged_all', 'boolean', label='TestUnloggedAll', comment='TESTS (plugin/config defined)', default=True))
    dynamic_flds.append(Field('configured_logged', 'boolean', label='TestConfiguredLogged', comment='', default=True))
    dynamic_flds.append(Field('all_tests', 'boolean', label='all tests bellow (from tests_splinter.py)', comment='TESTS (developer/code defined)', default=True))
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


def ensure_users():
    """
        this will insert into the test database(!) users from private/appconfig.ini, [splinter], ensure_users=
        format is: ensure_users = usr1, usr2, ..  where usrN is username or email or username#group or email#group
        obligatory auth_user fields (first_name, last_name, email) will be added automatically
        for additional obligatory auth_user fields please use request.vars
    """
    if not session.testdb or db is db0:     # this action is to danger ...
        redirect(URL('default', 'index'))   # ... if this is not the testing database then disable this call

    if 'username' in request.vars:  # additional fields for db.auth_user.insert()
        del request.vars['username']
    if 'password' in request.vars:
        del request.vars['password']

    for usrgrp in request.args:
        usrgrp = (base64.b32decode(usrgrp) + '#').split('#')
        usr = usrgrp[0]
        grp = usrgrp[1]

        try:
            row = db(db.auth_user.username == usr).select().first()
            username_used = True
        except AttributeError:
            row = db(db.auth_user.email == usr).select().first()
            username_used = False

        usr_id = None
        NAME_PREFIX = 'plugin_splinter_'
        if row:
            if row.last_name[:len(NAME_PREFIX)] == NAME_PREFIX:
                usr_id = row.id
            else:
                # we must delete the user, because we need to know the password (we will use TEST_PWD)
                if username_used:
                    db(db.auth_user.username == usr).delete()
                else:
                    db(db.auth_user.email == usr).delete()

        if usr_id is None:
            pwd = db.auth_user.password.validate(TEST_PWD)[0]  # convert plain value into database value (validator returns tuple like: (converted, problem) )
            usrflds = request.vars.copy()
            usrflds['first_name'] = usrflds.get('first_name', usr)
            usrflds['last_name'] = usrflds.get('last_name', NAME_PREFIX + usr)  # plugin_splinter_.. users will have TEST_PWD password already
            if username_used:
                if 'email' in usrflds:
                    email = usrflds['email']
                    del usrflds['email']
                else:
                    email = usr + '@' + NAME_PREFIX + 'domain.com'
                usr_id = db.auth_user.insert(username=usr, password=pwd, email=email, **usrflds)
            else:
                usr_id = db.auth_user.insert(email=usr, password=pwd, **usrflds)

        if grp:
            grp_id = db(db.auth_group.role == grp).select(db.auth_group.id).first()
            if not grp_id:
                grp_id = db.auth_group.insert(role=grp)
            if not db((db.auth_membership.user_id == usr_id) & (db.auth_membership.group_id == grp_id)).select().first():
                db.auth_membership.insert(user_id=usr_id, group_id=grp_id)

    redirect(URL('default', 'index'))
