# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip (into path from CHROME_PATH) current chromedriver
# run the server which shell be tested

# in private/appconfig.ini: [splinter] section, chromedriver= (pathname of chromedriver binary (download/unzip from google))
# in private/appconfig.ini: [splinter] section, production= (url of the production web incl. app)
# modules/tests_splinter.py must contain list TESTCLASSES with strings: names of testing classes

from splinter import Browser
# from tests_splinter import TESTCLASSES   # later: import from tests_splinter requires the TestBase class


class TestBase(object):
    def __init__(self, br, url):
        self.br = br
        self.url = url

from tests_splinter import TESTCLASSES
from tests_splinter import *  # test classes


def run_for_server(url, frmvars, myconf):
    print 'SERVER : ' + url
    print

    if frmvars.chrome:
        CHROME_PATH = {'executable_path': myconf.take('splinter.chromedriver')}
        run_for_browser(url, frmvars, 'chrome', CHROME_PATH)
    if frmvars.firefox:
        run_for_browser(url, frmvars, 'firefox')

    print 'FINISHED'

def run_for_browser(url, frmvars, browser, extra_params=None):
    if extra_params is None:
        extra_params = {}

    print 4*' ' + 'BROWSER : ' + browser
    print

    br = Browser(browser, **extra_params)

    for testClass in TESTCLASSES:
        if frmvars.all_tests or getattr(frmvars, 'test_' + testClass, False):
            print 8*' ' + 'TEST : ' + testClass

            testObj = globals()[testClass](br, url)
            testObj.run()

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
    assert(br.is_text_present('Contact'))
    bye()


def runTests():
    print 'testLogin'
    testLogin()


if __name__ == '__main__':
    run_for_browser('http://localhost:8000', None, 'firefox')
