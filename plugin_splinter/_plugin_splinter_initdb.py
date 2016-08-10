# -*- coding: utf-8 -*-

"""
for plugin_splinter, to establish database fixtures (initial data)

methods here can be called
    - in config defined test TestConfiguredUsers, if appconfig.ini [splinter] user_<user>= items are defined and !.. used in them
    - explicitly (use .run()) from user defined _plugin_splinter_tests

IMPORTANT: start each method with: db = current.db

It is recommended to use run() method to call other methods by their name, because:
    - it will check if changes are made to the TESTING database
    - DAL commands (usually insert-s) will be auto-commited

"""

from posixpath import join as urljoin
import uuid

from gluon import current

from plugin_splinter import REMOTE_DONE


# InitDb.run() runs locally
class InitDb(object):
    def run(self, testobj, testdb_func):
        token = str(uuid.uuid4())
        suburl = URL(a='x', c='plugin_splinter', f='init_testingdb', args=(token, testdb_func))[3:]
        self.check_page(suburl, check_text=REMOTE_DONE + token)

# next functions run remote and for TESTING database only
def init_testdb(testdb_func, db=None, db0=None):
    if db is None:
        db = current.db
    if db0 is None:
        db0 = current.db0
    assert db is not db0   # TESTING database?

    eval(testdb_func)()

    db.commit()

# here defined functions will be called via plugin_splinter/init_testingdb url and init_testdb(testdb_func)
# def testdb_func(): db = current.db ; ....
