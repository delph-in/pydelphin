import unittest
from collections import OrderedDict
from delphin.mrs import Mrs
from delphin.mrs.components import (
    Hook, ElementaryPredication as EP, Pred, Argument, MrsVariable, Lnk, qeq
)
from delphin.mrs import simplemrs
from delphin.mrs.simplemrs import tokenize # for convenience
from delphin._exceptions import XmrsDeserializationError as XDE

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
        eq = self.assertEqual
        t = lambda x: list(tokenize(x))  # convert to list for comparisons
        eq(t('[A:a0]'), ['[','A',':','a0',']'])
        eq(t('[ABC:abc1[abc D:d E3F:g]]'),
            ['[','ABC',':','abc1','[','abc','D',':','d', 'E3F',':','g',']',']'])
        # don't break up quoted sequences
        eq(t('"one [ two:2 ] three"A:a'),
            ['"one [ two:2 ] three"', 'A', ':', 'a'])
        eq(t(r'"a \"quote\""'), [r'"a \"quote\""'])
        # punctuation in lnks
        eq(t('<1:2>'), ['<','1',':','2','>'])
        eq(t('<1#2>'), ['<','1','#','2','>'])
        eq(t('<1 2>'), ['<','1','2','>'])
        eq(t('<@1>'), ['<','@','1','>'])
        eq(t('<>'), ['<','>'])
        # other punctuation non-breaking
        eq(t('<1!$%^&*()2>'), ['<','1!$%^&*()2','>'])
        # spacing doesn't matter much
        eq(t('[\n\nA     :\na]'), ['[','A',':','a',']'])
        # full test
        eq(t(compact_mrs), t(regular_mrs))

    def test_validate_token(self):
        eq = self.assertEqual
        eq(simplemrs.validate_token('ARG0','ARG0'), None)
        eq(simplemrs.validate_token('arg0','ARG0'), None)
        self.assertRaises(XDE, simplemrs.validate_token, 'ARG0', '[')

    def test_is_variable(self):
        eq = self.assertEqual
        is_var = simplemrs.is_variable
        eq(is_var('h5'), True)
        eq(is_var('hi'), False)
        eq(is_var(''), False)
        eq(is_var('h5_n_rel'), False)

class TestDeserialize(unittest.TestCase):
    def setUp(self):
        self.vars1 = {'h0': MrsVariable(vid=0, sort='h'),
                 'e1': MrsVariable(vid=1, sort='e', properties=OrderedDict(
                     SF='prop', TENSE='pres', MOOD='indicative',
                     PROG='-', PERF='-')),
                 'x2': MrsVariable(vid=2, sort='x', properties=OrderedDict(
                     PERS='3', NUM='pl', IND='+')),
                 'h3': MrsVariable(vid=3, sort='h'),
                 'h4': MrsVariable(vid=4, sort='h'),
                 'h5': MrsVariable(vid=5, sort='h'),
                 'h6': MrsVariable(vid=6, sort='h'),
                 'h7': MrsVariable(vid=7, sort='h')
                }
        self.mrs1ep1 = EP(Pred.grammarpred('udef_q_rel'),
                          self.vars1['h3'],
                          args=[Argument.mrs_argument('ARG0', self.vars1['x2']),
                                Argument.mrs_argument('RSTR', self.vars1['h4']),
                                Argument.mrs_argument('BODY', self.vars1['h5'])],
                          lnk=Lnk.charspan(0, 4))
        self.mrs1ep2 = EP(Pred.stringpred('"_dog_n_1_rel"'),
                          self.vars1['h6'],
                          args=[Argument.mrs_argument('ARG0', self.vars1['x2'])],
                          lnk=Lnk.charspan(0, 4))
        self.mrs1ep3 = EP(Pred.stringpred('"_sleep_v_1_rel"'),
                          self.vars1['h7'],
                          args=[Argument.mrs_argument('ARG0', self.vars1['e1']),
                                Argument.mrs_argument('ARG1', self.vars1['x2'])],
                          lnk=Lnk.charspan(5, 11))
        self.mrs1 = Mrs(
            hook=Hook(ltop=self.vars1['h0'], index=self.vars1['e1']),
            rels=[self.mrs1ep1, self.mrs1ep2, self.mrs1ep3],
            hcons=[qeq(self.vars1['h4'], self.vars1['h6'])]
        )

    def test_read_featval(self):
        eq = self.assertEqual
        rfv = simplemrs.read_featval
        eq(rfv(tokenize('CARG: "Kim"')), ('CARG', '"Kim"'))
        eq(rfv(tokenize('CARG: 3')), ('CARG', '3'))
        eq(rfv(tokenize('LBL: h1'), feat='LBL', sort='h'),
           ('LBL', MrsVariable(vid=1, sort='h')))
        self.assertRaises(XDE, rfv, tokenize('LBL: h1'), feat='ARG1')
        self.assertRaises(XDE, rfv, tokenize('LBL: h1'), sort='x')
        props = OrderedDict(PROP='val')
        eq(rfv(tokenize('ARG1: x1 [ x PROP: val ]')),
           ('ARG1', MrsVariable(vid=1, sort='x', properties=props)))

    def test_read_variable(self):
        eq = self.assertEqual
        rv = simplemrs.read_variable
        eq(rv(tokenize('h1')), MrsVariable(vid=1, sort='h'))
        eq(rv(tokenize('x1 [ x PROP: val ]')),
           MrsVariable(vid=1, sort='x', properties=OrderedDict(PROP='val')))
        self.assertRaises(XDE, rv, tokenize('x1 [ e PROP: val ]'))
        self.assertRaises(XDE, rv, tokenize('h1 [ h PROP: val ]'))
        self.assertRaises(XDE, rv, tokenize('x1'),
                          variables={'1':MrsVariable(vid=1, sort='h')})

    def test_read_props(self):
        pass

    def test_read_rels(self):
        eq = self.assertEqual
        read_rels = simplemrs.read_rels
        rr = lambda s: read_rels(tokenize(s))
        eq(rr('RELS: <>'), [])
        eq(rr('RELS: < [ udef_q_rel<0:4> LBL: h3 ARG0: x2 '
              '[ x PERS: 3 NUM: pl IND: + ] RSTR: h4 BODY: h5 ] >'),
           [self.mrs1ep1])
        eq(rr('RELS: < [ udef_q_rel<0:4> LBL: h3 ARG0: x2 '
              '[ x PERS: 3 NUM: pl IND: + ] RSTR: h4 BODY: h5 ] '
              '[ "_dog_n_1_rel"<0:4> LBL: h6 ARG0: x2 ] >'),
           [self.mrs1ep1, self.mrs1ep2])
        eq(rr('RELS: < [ udef_q_rel<0:4> LBL: h3 ARG0: x2 '
              '[ x PERS: 3 NUM: pl IND: + ] RSTR: h4 BODY: h5 ] '
              '[ "_dog_n_1_rel"<0:4> LBL: h6 ARG0: x2 ] '
              '[ "_sleep_v_1_rel"<5:11> LBL: h7 ARG0: e1 [ e SF: prop '
              'TENSE: pres MOOD: indicative PROG: - PERF: - ] ARG1: x2 ] >'),
           [self.mrs1ep1, self.mrs1ep2, self.mrs1ep3])
        #TODO: test missing >, etc.

    def test_read_ep(self):
        eq = self.assertEqual
        read_ep = simplemrs.read_ep
        rep = lambda s: read_ep(tokenize(s))
        #TODO self.assertRaises(XDE, rep, '[ ]')
        eq(rep('[ udef_q_rel<0:4> LBL: h3 ARG0: x2 '
               '[ x PERS: 3 NUM: pl IND: + ] RSTR: h4 BODY: h5 ]'),
           self.mrs1ep1)
        eq(rep('[ "_dog_n_1_rel"<0:4> LBL: h6 ARG0: x2 '
               '[ x PERS: 3 NUM: pl IND: + ] ]'), self.mrs1ep2)
        eq(rep('[ "_sleep_v_1_rel"<5:11> LBL: h7 ARG0: e1 [ e SF: prop '
               'TENSE: pres MOOD: indicative PROG: - PERF: - ] ARG1: x2 ]'),
           self.mrs1ep3)

    def test_read_lnk(self):
        eq = self.assertEqual
        rl = simplemrs.read_lnk
        eq(rl(tokenize('<>')), None)
        eq(rl(tokenize('<0:1>')), Lnk.charspan(0,1))
        eq(rl(tokenize('<@1>')), Lnk.edge(1))
        eq(rl(tokenize('<0#1>')), Lnk.chartspan(0,1))
        eq(rl(tokenize('<1>')), Lnk.tokens([1]))
        eq(rl(tokenize('<1 2 3>')), Lnk.tokens([1,2,3]))

    def test_read_hcons(self):
        pass
    def test_read_mrs(self):
        return
        #m = simplemrs.decode(regular_mrs)
        #eq(m.ltop, simplemrs.decode_handle('h0'))
