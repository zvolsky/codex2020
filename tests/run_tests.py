# -*- coding: utf-8 -*-

# http://www.web2py.com/AlterEgo/default/show/260
# https://groups.google.com/forum/#!searchin/web2py/unittest/web2py/lADMcdO84cY/56REY-gtGZwJ
# https://groups.google.com/forum/#!searchin/web2py/unittest/web2py/N4UT5GbTdlM/0IwUrH-w0acJ
#     testRunner code can be found on web2pyslices.com

import os
import glob
import sys
import unittest


APP = 'codex2020'


def run_tests(filename='test*.py'):
    app_root = os.path.join(os.getcwd(), 'applications', APP)
    files = os.path.join(app_root, 'tests', filename)
    db = DAL(myconf.take('db.testuri'), pool_size=myconf.take('db.pool_size', cast=int), check_reserved=['all'])
    suite = unittest.TestSuite()
    for file in glob.glob(files):
        execfile(file, locals())
    unittest.TextTestRunner(verbosity=2).run(suite)

#       (first version cannot be used as long we use/set db=DAL() in run_tests)
# python applications/codex2020/tests/run_tests.py filename.py  # selected test independent on app environment
# python web2py.py -S codex2020 -M -R applications/codex2020/tests/run_tests.py                 # all tests
# python web2py.py -S codex2020 -M -R applications/codex2020/tests/run_tests.py -A filename.py  # selected test
if __name__ == '__main__':
    if len(sys.argv) >= 2:
        run_tests(sys.argv[1])
    else:
        run_tests()
