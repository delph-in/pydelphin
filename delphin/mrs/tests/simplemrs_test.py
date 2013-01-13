import from delphin.mrs import simplemrs
import unittest

compact_mrs = r'[LTOP:h1 INDEX:e2[e SF:PROP-OR-QUES TENSE:TENSE]RELS:<' +\
              r'[exist_q_rel<0:4>LBL:h3 ARG0:x4[x PERS:3 NUM:PL] RSTR:h5' +\
              r'BODY:h6] "_dog_n_1_rel"<0:4>LBL:h7 ARG0:x4]' +\
              r'[_sleep_v_1_rel<5:9>

class TestDecoding(unittest.TestCase):
    def test_tokenize(self):
        self.assertEqual(simplemrs.tokenize(compact_mrs)
