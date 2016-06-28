# -*- coding: utf-8 -*-

import unittest

class TestBooks(unittest.TestCase):
    knownEan2isbn10 = (('9788072038022', '8072038028'),
                       ('9788072038024', '8072038028'),
                       ('9788020409836', '8020409831'))

    def testEan2isbn10(self):
        for vin, vout in self.knownEan2isbn10:
            result = roman.toRoman(integer)
            self.assertEqual(vout, result)

'''
# testFoo.py
execfile('applications/myapp/models/foo/0.py')
class TestFoo(unittest.TestCase):
	def setUp(self):
		pass
	def test_foobar(self):
		# put in whatever tests
self.assertTrue(True)
suite.addTest(unittest.makeSuite(TestFoo))
'''

'''
import unittest

from gluon.globals import Request

execfile("applications/api/controllers/10.py", globals())

db(db.game.id>0).delete()  # Clear the database
db.commit()

class TestListActiveGames(unittest.TestCase):
    def setUp(self):
        request = Request()  # Use a clean Request object

    def testListActiveGames(self):
        # Set variables for the test function
        request.post_vars["game_id"] = 1
        request.post_vars["username"] = "spiffytech"

        resp = list_active_games()
        db.commit()
        self.assertEquals(0, len(resp["games"]))

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(TestListActiveGames))
unittest.TextTestRunner(verbosity=2).run(suite)
'''