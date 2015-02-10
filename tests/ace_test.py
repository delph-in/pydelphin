import unittest

from delphin.interfaces import ace

class aceTest(unittest.TestCase):

    def testMissingGrammarThrowsException(self):
        with self.assertRaises(ValueError):
            ace.parse("myMissingGrammar", "Hello World!")
