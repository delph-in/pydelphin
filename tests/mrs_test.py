# -*- coding: UTF-8 -*-
from collections import OrderedDict
import unittest
from delphin.mrs import (Xmrs, Mrs, Dmrs, ElementaryPredication, Node, Pred,
                         Argument, Link, MrsVariable, HandleConstraint, Lnk,
                         Hook)
from delphin.mrs.config import (QEQ, LHEQ, OUTSCOPES,
                                EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST,
                                CHARSPAN, CHARTSPAN, TOKENS, EDGE,
                                GRAMMARPRED, REALPRED, STRINGPRED,
                                LTOP_NODEID, FIRST_NODEID)

class TestLnk(unittest.TestCase):
    def testLnkTypes(self):
        # invalid Lnk type
        self.assertRaises(ValueError, Lnk, data=(0,1), type='invalid')
        self.assertRaises(ValueError, Lnk, data=(0,1), type=None)

    def testCharSpanLnk(self):
        lnk = Lnk.charspan(0, 1)
        self.assertEqual(lnk.type, CHARSPAN)
        self.assertEqual(lnk.data, (0,1))
        lnk = Lnk.charspan('0', '1')
        self.assertEqual(lnk.data, (0,1))
        self.assertRaises(TypeError, Lnk.charspan, 1)
        self.assertRaises(TypeError, Lnk.charspan, [1])
        self.assertRaises(TypeError, Lnk.charspan, 1, 2, 3)
        self.assertRaises(ValueError, Lnk.charspan, 'a', 'b')

    def testChartSpanLnk(self):
        lnk = Lnk.chartspan(0, 1)
        self.assertEqual(lnk.type, CHARTSPAN)
        self.assertEqual(lnk.data, (0,1))
        lnk = Lnk.chartspan('0', '1')
        self.assertEqual(lnk.data, (0,1))
        self.assertRaises(TypeError, Lnk.chartspan, 1)
        self.assertRaises(TypeError, Lnk.chartspan, [1])
        self.assertRaises(TypeError, Lnk.chartspan, 1, 2, 3)
        self.assertRaises(ValueError, Lnk.chartspan, 'a', 'b')

    def testTokensLnk(self):
        lnk = Lnk.tokens([1, 2, 3])
        self.assertEqual(lnk.type, TOKENS)
        self.assertEqual(lnk.data, (1,2,3))
        lnk = Lnk.tokens(['1'])
        self.assertEqual(lnk.data, (1,))
        # empty tokens list might be invalid, but accept for now
        lnk = Lnk.tokens([])
        self.assertEqual(lnk.data, tuple())
        self.assertRaises(TypeError, Lnk.tokens, 1)
        self.assertRaises(ValueError, Lnk.tokens, ['a','b'])

    def testEdgeLnk(self):
        lnk = Lnk.edge(1)
        self.assertEqual(lnk.type, EDGE)
        self.assertEqual(lnk.data, 1)
        lnk = Lnk.edge('1')
        self.assertEqual(lnk.data, 1)
        self.assertRaises(TypeError, Lnk.edge, None)
        self.assertRaises(TypeError, Lnk.edge, (1,))
        self.assertRaises(ValueError, Lnk.edge, 'a')

class TestPred(unittest.TestCase):
    def testGpred(self):
        p = Pred.grammarpred('pron_rel')
        self.assertEqual(p.type, GRAMMARPRED)
        self.assertEqual(p.string, 'pron_rel')
        self.assertEqual(p.lemma, 'pron')
        self.assertEqual(p.pos, None)
        self.assertEqual(p.sense, None)
        p = Pred.grammarpred('udef_q_rel')
        self.assertEqual(p.string, 'udef_q_rel')
        self.assertEqual(p.lemma, 'udef')
        self.assertEqual(p.pos, 'q')
        self.assertEqual(p.sense, None)
        p = Pred.grammarpred('abc_def_ghi_rel')
        self.assertEqual(p.type, GRAMMARPRED)
        self.assertEqual(p.string, 'abc_def_ghi_rel')
        # pos must be a single character, so we get abc_def, ghi, rel
        self.assertEqual(p.lemma, 'abc_def')
        self.assertEqual(p.pos, None)
        self.assertEqual(p.sense, 'ghi')

    def testSpred(self):
        p = Pred.stringpred('_dog_n_rel')
        self.assertEqual(p.type, STRINGPRED)
        self.assertEqual(p.string, '_dog_n_rel')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, None)
        p = Pred.stringpred('_犬_n_rel')
        self.assertEqual(p.type, STRINGPRED)
        self.assertEqual(p.string, '_犬_n_rel')
        self.assertEqual(p.lemma, '犬')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, None)
        p = Pred.stringpred('"_dog_n_1_rel"')
        self.assertEqual(p.type, STRINGPRED)
        self.assertEqual(p.string, '"_dog_n_1_rel"')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, '1')
        #TODO: the following shouldn't throw warnings.. the code should
        # be more robust, but there should be some Warning or logging
        #self.assertRaises(ValueError, Pred.stringpred, '_dog_rel')
        #self.assertRaises(ValueError, Pred.stringpred, '_dog_n_1_2_rel')

    def testStringOrGrammarPred(self):
        p = Pred.string_or_grammar_pred('_dog_n_rel')
        self.assertEqual(p.type, STRINGPRED)
        p = Pred.string_or_grammar_pred('pron_rel')
        self.assertEqual(p.type, GRAMMARPRED)

    def testRealPred(self):
        # basic, no sense arg
        p = Pred.realpred('dog', 'n')
        self.assertEqual(p.type, REALPRED)
        self.assertEqual(p.string, '_dog_n_rel')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, None)
        # try with arg names, unicode, and sense
        p = Pred.realpred(lemma='犬', pos='n', sense='1')
        self.assertEqual(p.type, REALPRED)
        self.assertEqual(p.string, '_犬_n_1_rel')
        self.assertEqual(p.lemma, '犬')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, '1')
        # in case sense is int, not str
        p = Pred.realpred('dog', 'n', 1)
        self.assertEqual(p.type, REALPRED)
        self.assertEqual(p.string, '_dog_n_1_rel')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, '1')
        self.assertRaises(TypeError, Pred.realpred, lemma='dog')
        self.assertRaises(TypeError, Pred.realpred, pos='n')

    def testEq(self):
        self.assertEqual(Pred.stringpred('_dog_n_rel'),
                         Pred.realpred(lemma='dog', pos='n'))
        self.assertEqual(Pred.stringpred('_dog_n_rel'), '_dog_n_rel')
        self.assertEqual('_dog_n_rel', Pred.realpred(lemma='dog', pos='n'))
        self.assertEqual(Pred.stringpred('"_dog_n_rel"'),
                         Pred.stringpred("'_dog_n_rel'"))
        self.assertEqual(Pred.grammarpred('pron_rel'), 'pron_rel')
        self.assertNotEqual(Pred.string_or_grammar_pred('_dog_n_rel'),
                            Pred.string_or_grammar_pred('dog_n_rel'))

class TestNode(unittest.TestCase):
    def test_basic(self):
        # minimum is a nodeid and a pred
        self.assertRaises(TypeError, Node)
        self.assertRaises(TypeError, Node, 10000)
        n = Node(10000, Pred.stringpred('_dog_n_rel'))
        self.assertEqual(n.nodeid, 10000)
        self.assertEqual(n.pred, '_dog_n_rel')
        self.assertEqual(len(n.sortinfo), 0)
        self.assertEqual(n.lnk, None)
        self.assertEqual(n.surface, None)
        self.assertEqual(n.base, None)
        self.assertEqual(n.carg, None)
        self.assertEqual(n.cvarsort, None)
        self.assertEqual(len(n.properties), 0)
        self.assertFalse(n.is_quantifier())
        n = Node(10000, Pred.grammarpred('def_q_rel'))
        self.assertTrue(n.is_quantifier())

    def test_normal(self):
        n = Node(10000, Pred.stringpred('_dog_n_rel'),
                 sortinfo=OrderedDict(cvarsort='x', PER='3'),
                 lnk=Lnk.charspan(0,2))
        self.assertEqual(n.nodeid, 10000)
        self.assertEqual(n.pred, '_dog_n_rel')
        self.assertEqual(len(n.sortinfo), 2)
        self.assertEqual(n.cfrom, 0)
        self.assertEqual(n.cto, 2)
        self.assertEqual(n.surface, None)
        self.assertEqual(n.base, None)
        self.assertEqual(n.carg, None)
        self.assertEqual(n.cvarsort, 'x')
        self.assertEqual(len(n.properties), 1)
        self.assertEqual(n.properties['PER'], '3')
        self.assertFalse(n.is_quantifier())

#class TestElementaryPredication(unittest.TestCase):
#    def test_basic(self):
#        EP = ElementaryPredication
#        # minimum EP has pred
#        self.assertRaises(TypeError, EP)
#        self.assertRaises(TypeError, EP, )

#class TestXmrs(unittest.TestCase):
#    def test_empty(self):
#        x = Xmrs()
#        self.assertEqual(x.hook, None)
#        self.assertEqual(x.nodes, [])
#        self.assertEqual(x.rels, [])
#        self.assertEqual(x.eps, [])
#        self.assertEqual(x.args, [])
#        self.assertEqual(x.icons, [])

#class TestXmrsLinks(unittest.TestCase):
#    def setUp(self):
#        ltop = MrsVariable(0,'h')
#        sleep_cv = MrsVariable(1,'e')
#        sleep_lbl = MrsVariable(2, 'h')
#        dog_lbl = MrsVariable(3, 'h')
#        dog_cv = MrsVariable(4, 'x')
#        a_lbl = MrsVariable(5, 'h')
#        a_hole = MrsVariable(6, 'h')
#        a_body = MrsVariable(7, 'h')
#        big_lbl = MrsVariable(8, 'h')
#        big_cv = MrsVariable(9, 'e')
#
#        self.xmrs = Xmrs(
#            hook=Hook(ltop=ltop,index=sleep_cv),
#            nodes=[Node(10000, Pred.stringpred('_a_q_rel')),
#                   Node(10001, Pred.stringpred('_big_a_1_rel')),
#                   Node(10002, Pred.stringpred('_dog_n_1_rel')),
#                   Node(10003, Pred.stringpred('_sleep_v_1_rel'))],
#            args=[Argument(10000, 'RSTR', a_hole),
#                  Argument(10000, 'BODY', a_body),
#                  Argument(10001, 'ARG1', dog_cv),
#                  Argument(10003, 'ARG1', dog_cv)],
#            hcons=[HandleConstraint(ltop, QEQ, sleep_lbl),
#                   HandleConstraint(a_hole, QEQ, dog_lbl)],
#            cvs=[(10000, dog_cv), (10001, big_cv), (10002, dog_cv),
#                 (10003, sleep_cv)],
#            labels=[(10000, a_lbl), (10001, dog_lbl), (10002, dog_lbl),
#                    (10003, sleep_lbl)])
#
#    def test_argument_links(self):
#        labelsets = self.xlabelsets
#        self.assertEqual(labelsets,
#                         {'0': {LTOP_NODEID}, '2':{10003},
#                          '3': {10001,10002}, '5':{10000}})
#        self.assertEqual(
#            sorted(self.x._argument_links(labelsets), key=lambda l: l.start),
#            sorted([Link(10000, 10002, 'RSTR', H_POST),
#                    Link(10001, 10002, 'ARG1', EQ_POST),
#                    Link(10003, 10002, 'ARG1', NEQ_POST)],
#                   key=lambda l: l.start)
#        )
#        self.assertEqual(labelsets,
#                         {'0': {LTOP_NODEID}, '2':{10003},
#                          '3': {}, '5':{10000}})
#
#    def test_ltop_link(self):
#        pass
#
#
#class TestMrs(unittest.TestCase):
#    def test_empty(self):
#        m = Mrs()
#        self.assertEqual(m.ltop, None)
#        self.assertEqual(m.index, None)
#        self.assertEqual(len(m.rels), 0)
#        #self.assertEqual(len(m.variables), 0)
#        self.assertEqual(len(m.hcons), 0)
#        self.assertEqual(len(m.icons), 0)
