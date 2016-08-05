# -*- coding: utf-8 -*-

"""
for plugin_splinter, to establish database fixtures (initial data)

methods here can be called
    - in config defined test TestConfiguredUsers, if appconfig.ini [splinter] initdb_<user>= items are defined
    - explicitly (use .initdb()) from user defined plugin_splinter_tests
start each method with: db = current.db

use initdb() method to call other methods by their name, because:
    - it will check if changes are made to the TESTING database
    - DAL commands (usually insert-s) will be auto-commited

"""

from gluon import current

class InitDb(object):
    def initdb(self, fixture_method, testdb_only=True, db=None, db0=None):
        if db is None:
            db = current.db
        if db0 is None:
            db0 = current.db0

        if testdb_only:
            assert db is not db0

        # call fixture_method here
        eval('self.%s')

        db.commit()

    # def fixture_method(): db = current.db; ....
