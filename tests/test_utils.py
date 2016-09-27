# -*- coding: utf-8 -*-

"""
    see test_books for few examples
"""

import os
import sys
import unittest

modules_path = os.path.join(app_root, 'modules')
sys.path.append(modules_path)

import c_utils


class TestUtils(unittest.TestCase):
    titles = (
            ('aaa', ('bbb', 'ccc'),
                    'aaa', [(' : ', 'bbb'), (' : ', 'ccc')]),
            ('aaa : bbb', ('ccc /', 'ddd'),
                    'aaa', [(' : ', 'bbb'), (' : ', 'ccc'), (' / ', 'ddd')]),
            ('aaa : bbb', ('ccc bbb +', 'aaa /', 'ccc'),
                    'aaa', [(' : ', 'bbb'), (' / ', 'ccc')]),
    )

    def testCorrectTitle(self):
        class Rec(object):  # for testCorrectTitle()
            def __init__(self, tin, sin):
                self.title = tin
                self.subtitles = sin

        for tin, sin, tout, sout in self.titles:
            rec = Rec(tin, sin)
            c_utils.title_correction(rec)
            self.assertEqual(rec.title, tout)
            self.assertEqual(rec.subtitles, sout)

suite.addTest(unittest.makeSuite(TestUtils))
