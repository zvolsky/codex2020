# -*- coding: utf-8 -*-

# for plugin_splinter
# TESTCLASSES defines the testing classes

from plugin_splinter import TestBase

TESTCLASSES = ['Aaa', 'Bbb']

class Aaa(TestBase):
    def run(self):
        self.testUnlogged()

    def testUnlogged(self):
        print 12*' ' + 'testUnlogged'

        self.br.visit(self.url)
        assert(self.br.is_text_present('codex'))

class Bbb(TestBase):
    def run(self):
        self.br.visit(self.url)
        assert(self.br.is_text_present('codex'))
