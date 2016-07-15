# -*- coding: utf-8 -*-

# pip install selenium
# pip install splinter
# download and unzip (into path from CHROME_PATH) current chromedriver
# run the server which shell be tested

from splinter import Browser

CHROME_PATH = {'executable_path': myconf.take('splinter.chromedriver')}


def run_for_server(url, frmvars):
    print 'SERVER : ' + url
    print

    if frmvars.chrome:
        run_for_browser(url, frmvars, 'chrome', CHROME_PATH)
    if frmvars.firefox:
        run_for_browser(url, frmvars, 'firefox')

def run_for_browser(url, frmvars, browser, extra_params=None):
    if extra_params is None:
        extra_params = {}

    print 'BROWSER : ' + browser
    print

    br = Browser(browser, **extra_params)
    br.visit(url)
    assert(br.is_text_present('Codex'))




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
    run_for_server('http://localhost:8000', None)
