# -*- coding: utf-8 -*-

"""
- this will run webtests in TESTING database (db.urit from appconfig.ini)
- use sessions inside database: session.connect(request, response, db=db)
    --or-- if you use shared file system sessions then always have same auth_user rows for used users in both databases

- pip install selenium
- pip install splinter
- download and unzip from google the current chromedriver

- in private/appconfig.ini: [db] section, urit= (testing database; connection string similar to uri=)
- in private/appconfig.ini: [splinter] section, chromedriver= (pathname of chromedriver binary)
- in private/appconfig.ini: [splinter] section, testgroup= (default group: admin) - see testgroupuser bellow
- in private/appconfig.ini: [splinter] section, server1=, server2=, ...
       serverN = url;testgroupuser;password
           url           : url of tested server (include application, which can be omitted if suppressed by routes)
           testgroupuser : name of the user of group defined in the testgroup= (default group: admin)
           password      : password of the user

- modules/tests_splinter.py must contain list TESTCLASSES with strings: names of testing classes
- tested server must be running
"""


import os
from posixpath import join as urljoin

from splinter import Browser
# from tests_splinter import TESTCLASSES   # later: import from tests_splinter requires the TestBase class

from gluon import current


TESTS_ARE_ON_MSG = 'TEST MODE IS ENABLED'
OLD_TESTS_MSG = 'Previous tests are active. If this is 100 % sure not truth, you can remove models/_tests.py (WARNING: If you do so and tests are still running, they will damage the main application database!)'
ENABLER = os.path.join(current.request.folder, 'models', '_tests.py')


class TestBase(object):
    def __init__(self, br, url):
        self.br = br
        self.url = url

    def log_test(self, test_name):
        self.log(5, 'TEST', test_name)

    @staticmethod
    def log(level, label, name):
        print level * 4 * ' ' + label + ' : ' + name
        print

    def check_page(self, urlpath, check_text='Copyright'):
        self.br.visit(urljoin(self.url, urlpath))
        if check_text:
            assert self.br.is_text_present(check_text)


from tests_splinter import TESTCLASSES
from tests_splinter import *  # test classes themselves (because of python problems with instantiatig classes from names - see #**)


class TestStatus(object):
    # set testing mode on this machine

    @staticmethod
    def tests_running(self):
        return os.path.isfile(ENABLER)

    @staticmethod
    def tests_off():
        if TestStatus.tests_running():
            os.remove(ENABLER)

    @staticmethod
    def tests_on():
        if TestStatus.tests_running():
            print OLD_TESTS_MSG
            return False
        with open(ENABLER, mode='w') as f:
            f.write('splinter_tests = True' + os.path.sep + 'splinter_ip = ' + current.request.ip + os.path.sep)
        return True

    # set testing mode on remote url

    @staticmethod
    def remote_testing_mode_on(br, url):
        test_obj = TestStatus.login(br, url)
        test_obj.check_page('plugin_splinter/testing_mode_on', check_text=None)
        enabled = br.is_text_present(TESTS_ARE_ON_MSG)
        TestStatus.logout(br, url, test_obj=test_obj)
        return enabled

    @staticmethod
    def remote_testing_mode_off(br, url):
        test_obj = TestStatus.login(br, url)
        test_obj.check_page('plugin_splinter/testing_mode_off')
        TestStatus.logout(br, url, test_obj=test_obj)

    @staticmethod
    def login(br, url):
        test_obj = TestBase(br, url)
        TestStatus.logout(br, url, test_obj=test_obj)
        test_obj.check_page('default/user/login')
        name_el = br.find_by_name('username')
        if not name_el:
            name_el = br.find_by_name('email')
        name_el.type('jmeno')
        br.find_by_name('password').type('heslo')
        return test_obj

    @staticmethod
    def logout(br, url, test_obj=None):
        if test_obj is None:
            test_obj = TestBase(br, url)
        test_obj.check_page('default/user/logout')


def get_tested_servers(myconf):
    tested_servers = []
    server_no = 1
    while True:
        fldname = 'server%s' % server_no
        try:
            server_settings = myconf.take('splinter.' + fldname)
        except BaseException:
            break
        server_settings = server_settings.split(';', 2)
        if len(server_settings) == 3:
            tested_servers.append({'fldname': fldname, 'url': server_settings[0],
                                   'user': server_settings[1], 'pwd': server_settings[2]})
        server_no += 1
    return tested_servers

def run_for_server(url, frmvars, myconf):
    TestBase.log(0, 'SERVER', url)

    if frmvars['chrome']:  # frmvars don't use Storage (frmvars.attr) syntax to allow Scheduler mode
        CHROME_PATH = {'executable_path': myconf.take('splinter.chromedriver')}
        run_for_browser(url, frmvars, 'chrome', CHROME_PATH)
    if frmvars['firefox']:
        run_for_browser(url, frmvars, 'firefox')

    print 'FINISHED'

def run_for_browser(url, frmvars, browser, extra_params=None):
    if extra_params is None:
        extra_params = {}

    TestBase.log(1, 'BROWSER', browser)

    br = Browser(browser, **extra_params)

    if TestStatus.remote_testing_mode_on(br, url):
        for TestClass in TESTCLASSES:
            if frmvars['all_tests'] or frmvars.get('test_' + testClass, False):
                TestBase.log(2, 'TESTCLASS', TestClass)

                test_obj = globals()[TestClass](br, url)  #** see imports
                test_obj.run()
        TestStatus.remote_testing_mode_off(br, url)

    br.quit()
    print



def login():
    br.visit(URLBASE)
    br.find_by_id('username_login').fill('test')
    br.find_by_id('password_login').fill('0f331d07fd4ea60ba7be4613e019421ace2f2b8b')
    br.find_by_id('linkSignIn').click()

def bye():
    br.quit()

def testLogin():
    login()
    assert br.is_text_present('Contact')
    bye()


def runTests():
    print 'testLogin'
    testLogin()


if __name__ == '__main__':
    run_for_browser('http://localhost:8000', None, 'firefox')
