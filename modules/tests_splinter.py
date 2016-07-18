# -*- coding: utf-8 -*-

# for plugin_splinter
# TESTCLASSES defines the testing classes

from posixpath import join as urljoin

from plugin_splinter import TestBase

TESTCLASSES = ['TestUnlogged']

class TestUnlogged(TestBase):
    def run(self):
        self.test_unlogged_default()

    def test_unlogged_default(self):
        self.log('test Unlogged Default')

        self.check_page('default/models', 'finished ok')
        self.check_page('default/index')
        self.check_page('default/home')
        self.check_page('default/theme')
        self.check_page('default/wiki')
        self.check_page('default/welcome')
        self.check_page('default/login_newdb')
        self.check_page('default/newdb')

class Bbb(TestBase):
    def run(self):
        self.br.visit(self.url)
        assert(self.br.is_text_present('codex'))
