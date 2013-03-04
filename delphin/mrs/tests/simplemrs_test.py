from .. import simplemrs
from .. import mrserrors
import unittest

# "dogs sleep." with ACE and the ERG
compact_mrs = '''[LTOP:h0 INDEX:e1[e SF:prop TENSE:pres MOOD:indicative \
PROG:- PERF:-]RELS:<[udef_q_rel<0:4>LBL:h3 ARG0:x2[x PERS:3 NUM:pl IND:+]\
RSTR:h4 BODY:h5]["_dog_n_1_rel"<0:4>LBL:h6 ARG0:x2]["_sleep_v_1_rel"<5:11>\
LBL:h7 ARG0:e1 ARG1:x2]>HCONS:<h4 qeq h6>]'''

# "dogs sleep." with ACE and the ERG
regular_mrs = '''[ LTOP: h0 INDEX: e1 [ e SF: prop TENSE: pres \
MOOD: indicative PROG: - PERF: - ] RELS: < [ udef_q_rel<0:4> LBL: h3 ARG0: x2 \
[ x PERS: 3 NUM: pl IND: + ] RSTR: h4 BODY: h5 ]  [ "_dog_n_1_rel"<0:4> \
LBL: h6 ARG0: x2 ] [ "_sleep_v_1_rel"<5:11> LBL: h7 ARG0: e1 ARG1: x2 ] > \
HCONS: < h4 qeq h6 > ]'''

# "all red dogs and three blue dogs maybe sleep soundly." with ACE and the ERG
stress_test_mrs = '''[ LTOP: h0 INDEX: e1 [ e SF: prop TENSE: pres \
MOOD: indicative PROG: - PERF: - ] RELS: < [ udef_q_rel<0:32> LBL: h3 ARG0: x2 \
[ x PERS: 3 NUM: pl ] RSTR: h4 BODY: h5 ]  [ _all_q_rel<0:3> LBL: h6 ARG0: x7 \
[ x PERS: 3 NUM: pl IND: + ] RSTR: h8 BODY: h9 ]  [ "_red_a_1_rel"<4:7> \
LBL: h10 ARG0: e11 [ e SF: prop TENSE: untensed MOOD: indicative ] ARG1: x7 ] \
[ "_dog_n_1_rel"<8:12> LBL: h10 ARG0: x7 ]  [ _and_c_rel<13:16> LBL: h12 \
ARG0: x2 L-INDEX: x7 R-INDEX: x13 [ x PERS: 3 NUM: pl IND: + ] ] \
[ udef_q_rel<17:22> LBL: h14 ARG0: x13 RSTR: h15 BODY: h16 ] \
[ card_rel<17:22> LBL: h17 CARG: "3" ARG0: e19 [ e SF: prop TENSE: untensed \
MOOD: indicative ] ARG1: x13 ]  [ "_blue_a_1_rel"<23:27> LBL: h17 ARG0: e20 \
[ e SF: prop TENSE: untensed MOOD: indicative ] ARG1: x13 ] \
[ "_dog_n_1_rel"<28:32> LBL: h17 ARG0: x13 ]  [ "_sleep_v_1_rel"<39:44> \
LBL: h21 ARG0: e1 ARG1: x2 ]  [ "_sound_a_1_rel"<45:53> LBL: h21 ARG0: e22 \
[ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: e1 ] >\
HCONS: < h4 qeq h12 h8 qeq h10 h15 qeq h17 > ]'''

class TestHelperFunctions(unittest.TestCase):
    def setUp(self):
        pass
        
    def test_tokenize(self):
        # break up punctuation and symbols
        t = simplemrs.tokenize
        self.assertEqual(t('[A:a0]'), ['[','A',':','a0',']'])
        self.assertEqual(t('[ABC:abc1[abc D:d E3F:g]]'),
            ['[','ABC',':','abc1','[','abc','D',':','d', 'E3F',':','g',']',']'])
        # don't break up quoted sequences
        self.assertEqual(t('"one [ two:2 ] three"A:a'),
            ['"one [ two:2 ] three"', 'A', ':', 'a'])
        self.assertEqual(t(r'"a \"quote\""'), [r'"a \"quote\""'])
        # punctuation in lnks
        self.assertEqual(t('<1:2>'), ['<','1',':','2','>'])
        self.assertEqual(t('<1#2>'), ['<','1','#','2','>'])
        self.assertEqual(t('<1 2>'), ['<','1','2','>'])
        self.assertEqual(t('<@1>'), ['<','@','1','>'])
        # other punctuation non-breaking
        self.assertEqual(t('<1!$%^&*()2>'), ['<','1!$%^&*()2','>'])
        # spacing doesn't matter much
        self.assertEqual(t('[\n\nA     :\na]'), ['[','A',':','a',']'])
        # full test
        self.assertEqual(t(compact_mrs), t(regular_mrs))
    
    def test_validate_token(self):
        self.assertEqual(simplemrs.validate_token('ARG0','ARG0'), None)
        self.assertEqual(simplemrs.validate_token('arg0','ARG0'), None)
        self.assertRaises(mrserrors.MrsDecodeError,
                          simplemrs.validate_token, 'ARG0', '[')
        
    def test_read_handle(self):
        pass
    def test_read_variable(self):
        pass
    def test_read_props(self):
        pass
    def test_read_rels(self):
        pass
    def test_read_ep(self):
        pass
    def test_read_lnk(self):
        pass
    def test_read_hcons(self):
        pass
    def test_decode_mrs(self):
        m = simplemrs.decode(regular_mrs)
        self.assertEqual(m.ltop, simplemrs.decode_handle('h0'))
