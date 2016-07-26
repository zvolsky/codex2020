# -*- coding: utf-8 -*-

"""
- this will run webtests in TESTING database (db.urit from appconfig.ini)
- use sessions inside database: session.connect(request, response, db=db)
    --or-- if you use shared file system sessions then always have same auth_user rows for used users in both databases

- pip install selenium
- pip install splinter
- download and unzip from google the current chromedriver
- tested server must be running

- in private/appconfig.ini: [db] section, urit= (testing database; connection string similar to uri=)
- in private/appconfig.ini: [splinter] section, chromedriver= (pathname of chromedriver binary)
- in private/appconfig.ini: [splinter] section, testgroup= (default group: admin) - see testgroupuser bellow
- in private/appconfig.ini: [splinter] section, server1=, server2=, ...
       serverN = url;testgroupuser;password
           url           : url of tested server (include application, which can be omitted if suppressed by routes)
           testgroupuser : name of the user of group defined in the testgroup= (default group: admin)
           password      : password of the user

- tests
    -- defined already in plugin (TestUnloggedAll,..)
        --- TestUnloggedAll will check all controller actions if the page contains USUAL_TEXT
            USUAL_TEXT default: Copyright ; or you can set it in private/appconfig.ini: [splinter] section, usual_text=

    -- user defined tests
        modules/tests_splinter.py must contain list TESTCLASSES with strings: names of testing classes
        each class must have run() method
"""


import os
import re
from posixpath import join as urljoin

from splinter import Browser
# from tests_splinter import TESTCLASSES   # later: import from tests_splinter requires the TestBase class

from gluon import current
from gluon.contrib.appconfig import AppConfig


myconf = AppConfig()

TESTS_ARE_ON_MSG = 'TEST MODE IS ENABLED'
TESTS_ARE_OFF_MSG = 'TEST MODE IS OFF -> STANDARD MODE'
OLD_TESTS_MSG = 'Previous tests are active. If this is 100 % sure not truth, you can remove models/_tests.py (WARNING: If you do so and tests are still running, they will damage the main application database!)'
try:
    USUAL_TEXT = myconf.take('splinter.usual_text')
except:
    USUAL_TEXT = 'Copyright'


class TestBase(object):
    def __init__(self, br, url):
        self.br = br
        self.url = url

    def log_test(self, test_name):
        self.log(3, 'TEST', test_name)

    @staticmethod
    def log(level, label, name):
        print level * 4 * ' ' + label + ' : ' + name
        print

    def check_page(self, urlpath, check_text=USUAL_TEXT, silent=False):
        self.br.visit(urljoin(self.url, urlpath))
        if check_text:
            result = self.br.is_text_present(check_text)
            if silent:
                return result
            else:
                assert result
        return True


from tests_splinter import TESTCLASSES
from tests_splinter import *  # test classes themselves (because of python problems with instantiatig classes from names - see #**)


class TestUnloggedAll(TestBase):
    def run(self):
        self.test_unlogged_all()

    def test_unlogged_all(self, appfolder=None, request=None):
        if appfolder is None:
            if request is None:
                request = current.request
            appfolder = request.folder

        self.log_test('TestUnloggedAll')

        try:
            ignored = myconf.take('splinter.ignore_unlogged')
        except:
            ignored = ''
        ignored = ignored.split(',')
        ignored = [action.strip() for action in ignored if action.strip()]
        failed = []

        for controller in os.listdir(urljoin(appfolder, 'controllers')):
            if controller[-3:] == '.py' and not controller == 'appadmin.py':
                controller_name = controller[:-3]
                self.log(4, 'controller', controller)
                with open(urljoin(appfolder, 'controllers', controller)) as hnd:
                    codelines = hnd.readlines()
                self.parse_controller(controller_name, codelines, ignored, failed)

        if failed:
            failed = ', '.join(failed)
            self.log(3, 'FAILED', failed)
            txt = 'If this is an expected (correct) result then you should modify private/appconfig.ini: '
            if ignored:
                self.log(3, 'TIP', txt + 'add new items into configuration item [splinter] ignore_unlogged = ...: ' + failed)
            else:
                self.log(3, 'TIP', txt + 'add an item [splinter] ignore_unlogged = ' + failed)
        else:
            self.log(3, 'OK', 'All tested actions render a page with a usual_text inside: ' + USUAL_TEXT)

    def parse_controller(self, controller_name, codelines, ignored, failed):
        skip_next = False
        for ln in codelines:
            ln = ln.rstrip()  # - \n

            if ln[:4] == 'def ' and ln[-3:] == '():':  # function without parameters, maybe Web2py action
                if skip_next:
                    skip_next = False
                else:
                    action = ln[4:-3].strip()
                    if action[:2] != '__':                 # Web2py action
                        url = urljoin(controller_name, action)
                        if not url in ignored:
                            self.log(5, 'action', action)
                            if not self.check_page(url, silent=True):
                                failed.append(url)
                                self.log(6, 'WARNING', 'Usual text is missing.')
            elif re.match('^#\s*ajax$', ln):   #  # ajax
                skip_next = True
            elif ln == '':
                skip_next = False


class TestStatus(object):
    # set testing mode on this machine

    def tests_running(self):
        session = current.session
        return session.testdb  # in (at least) models/db.py we use session.testdb directly

    def tests_off(self, session=None):
        session = current.session
        if self.tests_running():
            if 'auth' in session:
                del session.auth
            del session.testdb

    def tests_on(self, session=None):
        session = current.session
        if self.tests_running():
            print OLD_TESTS_MSG
            return False
        if 'auth' in session:
            del session.auth
        session.testdb = True
        return True

    # set testing mode on remote url

    @staticmethod
    def remote_testdb_on(br, server):
        test_obj = TestStatus.login(br, server)
        test_obj.check_page('plugin_splinter/testdb_on', check_text=None)
        enabled = br.is_text_present(TESTS_ARE_ON_MSG)
        return enabled

    @staticmethod
    def remote_testdb_off(br, server):
        test_obj = TestStatus.login(br, server)
        test_obj.check_page('plugin_splinter/testdb_off', check_text=TESTS_ARE_OFF_MSG)

    @staticmethod
    def login(br, server):
        url = server['url']
        test_obj = TestBase(br, url)
        TestStatus.logout(br, url, test_obj=test_obj)
        test_obj.check_page('default/user/login')
        name_el = br.find_by_name('username')
        if not name_el:
            name_el = br.find_by_name('email')
        # do not see any way how to configure user/pwd on the target server and safely use them from remote test
        #   so we store user/pwd (in the target servers list) on the controlling machine
        name_el.type(server['user'])
        br.find_by_name('password').type(server['pwd'])
        br.find_by_id('submit_record__row').find_by_tag('input').click()
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
            tested_servers.append({'fldname': fldname, 'url': server_settings[0].strip(),
                                   'user': server_settings[1].strip(), 'pwd': server_settings[2].strip()})
        server_no += 1
    return tested_servers

def run_for_server(server, frmvars, myconf):
    TestBase.log(0, 'SERVER', server['url'])

    if frmvars['chrome']:  # frmvars don't use Storage (frmvars.attr) syntax to allow Scheduler mode
        CHROME_PATH = {'executable_path': myconf.take('splinter.chromedriver')}
        run_for_browser(server, frmvars, 'chrome', CHROME_PATH)
    if frmvars['firefox']:
        run_for_browser(server, frmvars, 'firefox')

    print 'FINISHED'

def run_for_browser(server, frmvars, browser, extra_params=None):
    if extra_params is None:
        extra_params = {}

    TestBase.log(1, 'BROWSER', browser)

    br = Browser(browser, **extra_params)

    if TestStatus.remote_testdb_on(br, server):
        url = server['url']

        # default tests
        if frmvars.unlogged_all:
            TestBase.log(2, 'TESTCLASS', 'TestUnloggedAll')
            testObj = TestUnloggedAll(br, url)  # make instance of the class (how to ~ better in py?)
            testObj.run()

        # user defined tests from modules/tests_splinter
        for TestClass in TESTCLASSES:
            if frmvars['all_tests'] or frmvars.get('test_' + TestClass, False):
                TestBase.log(2, 'TESTCLASS', TestClass)

                test_obj = globals()[TestClass](br, url)  #** see imports
                test_obj.run()
        # seems not necessary and not good here: TestStatus.remote_testdb_off(br, server)
    else:
        TestBase.log(2, 'FATAL', 'Cannot log in.')

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
