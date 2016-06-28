# -*- coding: utf-8 -*-

import os
import glob
import sys
import unittest


APP = 'codex2020'


def run_tests(filename='test*.py'):
    files = os.path.join(os.getcwd(), 'applications', APP, 'tests', filename)
    db = DAL(myconf.take('dbtest.uri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'])
    suite = unittest.TestSuite()
    for file in glob.glob(files):
        execfile(file, globals())
    unittest.TextTestRunner(verbosity=2).run(suite)


# python applications/codex2020/tests/run_tests.py filename.py  # selected test independent on app environment
# python web2py.py -S codex2020 -M -R applications/codex2020/tests/run_tests.py                 # all tests
# python web2py.py -S codex2020 -M -R applications/codex2020/tests/run_tests.py -A filename.py  # selected test
if __name__ == '__main__':
    if len(sys.argv) >= 2:
        run_tests(sys.argv[1])
    else:
        run_tests()
