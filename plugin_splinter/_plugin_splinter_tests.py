# -*- coding: utf-8 -*-

# for plugin_splinter
# TESTCLASSES defines the testing classes

from plugin_splinter import TestBase

try:
    from _plugin_splinter_initdb import InitDb  # for methods which initialize testing database
except ImportError:
    pass

# there is no reason to use LocalCalls from here, because it is intended for config-defined (user_..=) tests
#   and you can define code directly here; however LocalCalls allow reuse code from some config-defined test here
try:
    from _plugin_splinter_localcalls import LocalCalls    # for test parts inside _plugin_splinter_localcalls
except ImportError:
    pass


# private/appconfig.ini[splinter]ensure_users= setting will cause inserting users into db.auth_user (in testing db)
#   in such case first_name, last_name, email are added automatically, but if validation requires MORE AUTH_USER fields
#   then enter such fields here, they will be used in db.auth_user.insert(..., **MORE_AUTH_USER_FIELDS)
MORE_AUTH_USER_FIELDS = {}
# example:  MORE_AUTH_USER_FIELDS = {'registered': datetime.datetime.now(), 'city': 'Paris'}


TESTCLASSES = ['TestUnlogged']

class TestUnlogged(TestBase):
    def run(self):
        # here you can load database fixture(s) via InitDb

        # here you can call self.ensure_users(<usr>) or (for all configured) .ensure_users()
        #   if validations in auth_user requires specific additional fields then you can either
        #       - insert user through fixture/InitDb; .ensure_users() will ensure the group membership only
        #       - set MORE_AUTH_USER_FIELDS dict; this dict will be appended in the db.auth_user.insert(...)

        self.test_unlogged_default()

    def test_unlogged_default(self):
        self.log_test('Unlogged Default')

        self.check_page('default/models', 'finished ok')
        self.check_page('default/index')
        self.check_page('default/theme')
        self.check_page('default/wiki')
        self.check_page('default/welcome')
        self.check_page('default/login_newdb')
        self.check_page('default/newdb')

class Bbb(TestBase):
    def run(self):
        self.br.visit(self.url)
        assert self.br.is_text_present('codex')
