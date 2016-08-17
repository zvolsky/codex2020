# -*- coding: utf-8 -*-

"""
for plugin_splinter, to call code-defined test parts from config-defined test

methods here can be called
    - in config defined test TestConfiguredUsers, if appconfig.ini [splinter] user_<user>= items are defined and ?.. used in them
    - explicitly (use .run()) from user defined _plugin_splinter_tests

IMPORTANT: each method needs br parameter (browser)

You can
    - use run() method for compatibility with _plugin_splinter_initdb
    - or call
    - it will check if changes are made to the TESTING database
    - DAL commands (usually insert-s) will be auto-commited

"""

class LocalCalls(object):
    def run(self, br, method):
        # call the method here
        retval = eval('self.%s')(br)
        return False if retval is False else True

    # def method(br): ....
