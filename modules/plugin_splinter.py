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
- if you want auto-create testing users, set in private/appconfig.ini: [splinter] section, ensure_users= usr1, usr2,..
        where usrN is: user (user without group membership) or user#group (user in group); user is username if it's used, otherwise email
        if db.auth_user_insert requires more obligatory fields as (first_name, last_name, email) you can set them in modules/tests_splinter.py using dictionary MORE_AUTH_USER_FIELDS
        password is 'a23456789' for all such users
        you can create users manually too (recommended password is 'a23456789'),
            however users mentioned in ensure_users= will be rewritten; to avoid this set the last_name: plugin_splinter_..

- tests
    -- defined already in plugin (tests based on user_/skip_ setting for unlogged user and for user_<user>/skip_<user> for defined users)
        --- TestActions will check all controller actions if the page contains [ USUAL_TEXT | text after $... ]
            user_= (unlogged) and user_<user>= settings defines tested urls
                controller/* (or *) will test all actions (all actions of all controllers) which AREN'T explicitly used in user_/skip_ settings of that user
                user_ items can terminate with $text1$text2... - test will check presence of such texts (implicit: from usual_text= if used else "Copyright")
            skip_= and skip_<user> will exclude actions from testing
            for unlogged user will @auth. decorated actions be skipped too

            Example:
                app actions are: default/index, default/home, default/user, students/list, students/edit
                appconfig.ini:
                    ensure_users = mary, joe#admin
                    user_ = default/*$Please log in.
                    skip_ = default/user
                    user_mary = *, students/edit/1?defaultteacher=Smith$Lastname$Teacher
                    skip_mary = default/user
                    user_joe = *$You have admin rights.
                means we test
                 - unlogged user: urls default/index, default/home for text Please log in. ; @auth. decorated will be skipped
                 - user mary: urls default/index, default/home, students/list for text Copyright, students/edit/.. for texts Lastname and Teacher
                 - user joe: all actions for text You have admin rights.

    -- user defined tests
        modules/tests_splinter.py must contain list TESTCLASSES with strings: names of testing classes
        each class must have run() method
"""


import base64
import os
import re
from posixpath import join as urljoin

from splinter import Browser
# from tests_splinter import TESTCLASSES, MORE_AUTH_USER_FIELDS   # later: import from tests_splinter requires the TestBase class

from gluon import current
from gluon.html import URL
from gluon.contrib.appconfig import AppConfig


myconf = AppConfig()

TESTS_ARE_ON_MSG = 'TEST MODE IS ENABLED'
TESTS_ARE_OFF_MSG = 'TEST MODE IS OFF -> STANDARD MODE'
OLD_TESTS_MSG = 'Previous tests are active. If this is 100 % sure not truth, you can remove models/_tests.py (WARNING: If you do so and tests are still running, they will damage the main application database!)'
NOT_CONFIGURED = ' - NOT CONFIGURED'

try:
    USUAL_TEXT = myconf.take('splinter.usual_text')
except:
    USUAL_TEXT = 'Copyright'

TEST_PWD = 'a23456789'


# base class for tests -----------------------------

class TestBase(object):
    def __init__(self, br, url):
        self.br = br
        self.url = url

    def log_test(self, test_name):
        self.log(3, 'TEST', test_name)

    def log_text(self, txt):
        self.log(4, txt)

    @staticmethod
    def log(level, label, name=None):
        lbl = level * 4 * ' ' + label
        if name is None:
            print lbl
        else:
            print lbl + ' : ' + name
        print

    def check_page(self, urlpath, check_text=USUAL_TEXT, silent=False, check_testingdb=True):
        """
            check_text: string or iterable of strings
        """
        self.br.visit(urljoin(self.url, urlpath))
        if check_testingdb and self.br.is_element_present_by_xpath('//div'):
            assert self.br.is_text_present('TESTING DATABASE'), "Not running on testing database. Apply recommended code patches for default/user, db=DAL() and inside layout.html (if session.testdb:)."
        if check_text:
            if isinstance(check_text, basestring):
                check_text = (check_text,)
            for txt in check_text:
                if txt:  # empty txt can come from parsed appconfig.ini [splinter] user_...
                    result = self.br.is_text_present(txt)
                    if silent:
                        if not result:
                            return result
                    else:
                        assert result
        return True

    def login(self, usr):
        TestStatus.login(self.br, {'url': self.url}, usr, TEST_PWD)

    # all actions (*) generator

    def controllers(self, appfolder):
        """
            yields names of all controllers (without .py) except off appadmin
        """
        for controller in os.listdir(urljoin(appfolder, 'controllers')):
            if controller[-3:] == '.py' and not controller == 'appadmin.py':
                yield controller[:-3]

    def get_controller_codelines(self, appfolder, controller):
        controller = controller.split('/')[0]  # <controller> or <controller/*> can be used
        with open(urljoin(appfolder, 'controllers', controller + '.py')) as hnd:
            codelines = hnd.readlines()
        return codelines

    def actions(self, appfolder, controller, skipped, skip_auth=False):
        """
        Generator.
        Parse codelines from controller code and yield '<controller>/<action>' strings.

        Args:
            appfolder: application folder
            controller: name of the controller (without .py) ['<controller>/*' will be converted into 'controller']
            skipped: list of actions we want to skip/ignore them
            skip_auth: if True, all @auth. decorated actions will be skipped too (useful for unlogged user)
        """
        controller = controller.split('/')[0]  # <controller> or <controller/*> can be used
        codelines = self.get_controller_codelines(appfolder, controller)
        skip_next = False
        for ln in codelines:
            ln = ln.rstrip()  # - \n

            if ln[:4] == 'def ' and ln[-3:] == '():':  # function without parameters, maybe Web2py action
                if skip_next:
                    skip_next = False
                else:
                    action = ln[4:-3].strip()
                    if action[:2] != '__':                 # Web2py action
                        url = urljoin(controller, action)
                        if not url in skipped:
                            yield url
            elif skip_auth and ln[:6] == '@auth.' or re.match('^#\s*ajax$', ln):   #  unlogged user + need authorize --or-- # ajax
                skip_next = True
            elif ln == '':
                skip_next = False

    def gen_urls(self, requested, skipped=None, skip_auth=False, usual_text="Copyright", appfolder=None, request=None):
        """
        Cycles through all actions and yields (url, (testedText1, testedText2, ..))

        Args:
            requested: list from user_...= setting (appconfig.ini [splinter])
            skipped: list from skip_...= setting (appconfig.ini [splinter])
            skip_auth: if True, actions preceded by @auth. will be skipped too (suitable for unlogged user)
            usual_text: testedText1 for user_.. items without $ (probably use the value from usual_text= setting)
        rare used:
            appfolder: [ explicit | implicit from request.folder ]
            request: (if appfolder is None only) [ explicit | implicit: current.request ]
        """
        explicitly_tested = []  # controller/action
        for url in requested:   # strip controller/action from maybe longer url
            parts = (url.replace('?', '/').replace('#', '/').replace('$', '/') + '//').split('/', 2)
            explicitly_tested.append(parts[0] + '/' + parts[1])

        if skipped is None:
            skipped = []
        skipped = skipped + explicitly_tested + ['plugin_splinter/testdb_on', 'plugin_splinter/testdb_off']

        if appfolder is None:
            if request is None:
                request = current.request
            appfolder = request.folder

        for url_item in requested:
            url_item_parts = url_item.split('$')
            url = url_item_parts[0]
            if url:
                if len(url_item_parts) == 1:
                    tested_texts = [usual_text]
                else:
                    tested_texts = []
                    for txt in url_item_parts[1:]:
                        if txt:
                            tested_texts.append(txt)
                if url[-1] != '*':
                    yield((url, tested_texts))
                elif url == '*':
                    for controller in self.controllers(appfolder):
                        for actionpath in self.actions(appfolder, controller, skipped, skip_auth):
                            yield((actionpath, tested_texts))
                elif '/' in url:  # controller/*
                    for actionpath in self.actions(appfolder, url, skipped, skip_auth):
                        yield((actionpath, tested_texts))


try:
    from tests_splinter import MORE_AUTH_USER_FIELDS
except ImportError:
    MORE_AUTH_USER_FIELDS = {}

try:
    from tests_splinter import TESTCLASSES
    from tests_splinter import *  # test classes themselves (because of python problems with instantiating classes from names - see #**)
except ImportError:
    TESTCLASSES = []


# plugin/appconfig defined tests -----------------------------

class TestConfiguredLogged(TestBase):
    def __init__(self, br, url, ensure_users):
        super(TestConfiguredLogged, self).__init__(br, url)
        self.ensure_users = ensure_users

    def run(self):
        for user_item in self.ensure_users:
            usr = user_item.split('#')[0]
            self.test_configured_user(usr)

    def test_configured_user(self, usr):
        try:
            user_tests = myconf.take('splinter.user_' + usr)
        except:
            user_tests = None

        test_pseudo_name = 'user: ' + usr
        if user_tests is None:
            self.log_test(test_pseudo_name + NOT_CONFIGURED)
            self.log_text('Configure private/appconfig.ini [splinter] user_' + usr
                         + ' = url1, url2,.. ; url1 = url1 | url1$txt1$txt2... (navigate to urlN and check text txtN (or usual_text=/"Copyright" if omitted))')
        else:
            self.login(usr)
            user_tests = user_tests.split(',')
            self.log_test(test_pseudo_name)
            for test_item in user_tests:
                if test_item.strip():
                    test_config = test_item.split('$')
                    urlpath = test_config[0].strip()
                    tested_texts = test_config[1:]
                    TestBase.log(4, urlpath, '; '.join(tested_texts) or USUAL_TEXT)
                    self.check_page(urlpath, check_text=tested_texts)


class TestUnloggedAll(TestBase):
    def run(self):
        for url, tested_texts in self.gen_urls(['default/home/xx?p=2$aa$bb $', 'default/*'], skipped=None, skip_auth=False, usual_text="Copyright"):
            print url, tested_texts

class xTestUnloggedAll(TestBase):
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
        except BaseException:
            ignored = ''
        ignored = ignored.split(',')
        ignored = [action.strip() for action in ignored if action.strip()]
        ignored_full = ignored + ['plugin_splinter/testdb_on', 'plugin_splinter/testdb_off']
        failed = []

        for controller in os.listdir(urljoin(appfolder, 'controllers')):
            if controller[-3:] == '.py' and not controller == 'appadmin.py':
                controller_name = controller[:-3]
                self.log(4, 'controller', controller)
                with open(urljoin(appfolder, 'controllers', controller)) as hnd:
                    codelines = hnd.readlines()
                self.parse_controller(controller_name, codelines, ignored_full, failed)

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

# test mode control -----------------------------

class TestStatus(object):
    # set testing mode on this machine

    def tests_running(self):
        session = current.session
        return session.testdb  # in (at least) models/db.py we use session.testdb directly

    def tests_off(self, session=None):
        session = current.session
        # if self.tests_running():  # we cannot test this here, because it is already cleared from login?next=
        if 'auth' in session:
            del session.auth
        if 'testdb' in session:     # maybe this is never true: see above ; but to be sure (what about if the user can be logged and login page is skipped?)
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
    def login(br, server, usr=None, pwd=None):
        pwd = pwd if usr else server['pwd']
        usr = usr or server['user']
        url = server['url']
        test_obj = TestBase(br, url)
        TestStatus.logout(br, url, test_obj=test_obj)
        test_obj.check_page('default/user/login', check_testingdb=False)
        name_el = br.find_by_name('username')
        if not name_el:
            name_el = br.find_by_name('email')
        # do not see any way how to configure user/pwd on the target server and safely use them from remote test
        #   so we store user/pwd (in the target servers list) on the controlling machine
        name_el.type(usr)
        br.find_by_name('password').type(pwd)
        br.find_by_id('submit_record__row').find_by_tag('input').click()
        return test_obj

    @staticmethod
    def logout(br, url, test_obj=None):
        """
        Args:
            test_obj: example: TestBase(br, url) ; can be reused if you have one already prepared
        """
        if test_obj is None:
            test_obj = TestBase(br, url)
        test_obj.check_page('default/user/logout', check_testingdb=False)


# starting of tests: server list, server, browser ---------------------------

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
    url = server['url']

    TestBase.log(1, 'BROWSER', browser)

    br = Browser(browser, **extra_params)

    if TestStatus.remote_testdb_on(br, server):
        try:
            ensure_users = myconf.take('splinter.ensure_users')
        except BaseException:
            ensure_users = None
        if ensure_users:
            ensure_users = ensure_users.split(',')
            ensure_users = [eusr.strip() for eusr in ensure_users]
            ensure_users_encoded = [base64.b32encode(eusr) for eusr in ensure_users]  # Web2py args failure?
            suburl = URL(a='x',c='plugin_splinter', f='ensure_users', args=ensure_users_encoded, vars=MORE_AUTH_USER_FIELDS)[3:]
            br.visit(urljoin(url, suburl))  # prepare user from [splinter]ensure_users= setting inside the testing database

        # default tests
        if frmvars['unlogged_all']:
            TestBase.log(2, 'TESTCLASS', 'TestUnloggedAll')
            testObj = TestUnloggedAll(br, url)
            testObj.run()
        if frmvars['configured_logged']:
            if ensure_users:
                TestBase.log(2, 'TESTCLASS', 'TestConfiguredLogged')
                testObj = TestConfiguredLogged(br, url, ensure_users)
                testObj.run()
            else:
                TestBase.log(2, 'TESTCLASS', 'TestConfiguredLogged' + NOT_CONFIGURED)
                TestBase.log(3, 'Configure private/appconfig.ini [splinter] ensure_users= usr1, usr2,.. ; usr1 = usr1 | usr1#grp1')

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


'''
if __name__ == '__main__':
    run_for_browser('http://localhost:8000', None, 'firefox')
'''
