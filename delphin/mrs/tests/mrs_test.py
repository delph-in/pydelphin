# -*- coding: UTF-8 -*-
from .. import Lnk, Pred, ElementaryPredication, Mrs
import unittest

class TestLnk(unittest.TestCase):
    def testLnkTypes(self):
        # invalid Lnk type
        self.assertRaises(ValueError, Lnk, data=(0,1), type='invalid')
        self.assertRaises(ValueError, Lnk, data=(0,1), type=None)

    def testCharSpanLnk(self):
        lnk = Lnk(data=(0,1), type=Lnk.CHARSPAN)
        self.assertEqual(lnk.type, Lnk.CHARSPAN)
        self.assertEqual(lnk.data, (0,1))
        lnk = Lnk(data=['0','1'], type=Lnk.CHARSPAN)
        self.assertEqual(lnk.data, (0,1))
        self.assertRaises(ValueError, Lnk, data=1, type=Lnk.CHARSPAN)
        self.assertRaises(ValueError, Lnk, data=[1], type=Lnk.CHARSPAN)
        self.assertRaises(ValueError, Lnk, data=[1,2,3], type=Lnk.CHARSPAN)
        self.assertRaises(ValueError, Lnk, data=['a','b'], type=Lnk.CHARSPAN)

    def testChartSpanLnk(self):
        lnk = Lnk(data=(0,1), type=Lnk.CHARTSPAN)
        self.assertEqual(lnk.type, Lnk.CHARTSPAN)
        self.assertEqual(lnk.data, (0,1))
        lnk = Lnk(data=['0','1'], type=Lnk.CHARTSPAN)
        self.assertEqual(lnk.data, (0,1))
        self.assertRaises(ValueError, Lnk, data=1, type=Lnk.CHARTSPAN)
        self.assertRaises(ValueError, Lnk, data=[1], type=Lnk.CHARTSPAN)
        self.assertRaises(ValueError, Lnk, data=[1,2,3], type=Lnk.CHARTSPAN)
        self.assertRaises(ValueError, Lnk, data=['a','b'],
                          type=Lnk.CHARTSPAN)

    def testTokensLnk(self):
        lnk = Lnk(data=(1,2,3), type=Lnk.TOKENS)
        self.assertEqual(lnk.type, Lnk.TOKENS)
        self.assertEqual(lnk.data, (1,2,3))
        lnk = Lnk(data=['1'], type=Lnk.TOKENS)
        self.assertEqual(lnk.data, (1,))
        self.assertRaises(ValueError, Lnk, data=1, type=Lnk.TOKENS)
        self.assertRaises(ValueError, Lnk, data=[], type=Lnk.TOKENS)
        self.assertRaises(ValueError, Lnk, data=['a','b'], type=Lnk.TOKENS)

    def testEdgeLnk(self):
        lnk = Lnk(data=1, type=Lnk.EDGE)
        self.assertEqual(lnk.type, Lnk.EDGE)
        self.assertEqual(lnk.data, 1)
        lnk = Lnk(data='1', type=Lnk.EDGE)
        self.assertEqual(lnk.data, 1)
        self.assertRaises(ValueError, Lnk, data=None, type=Lnk.EDGE)
        self.assertRaises(ValueError, Lnk, data=(1,), type=Lnk.EDGE)
        self.assertRaises(ValueError, Lnk, data='a', type=Lnk.EDGE)

class TestPred(unittest.TestCase):
    def testGpred(self):
        p = Pred('pron_rel')
        self.assertEqual(p.type, Pred.GPRED)
        self.assertEqual(p.string, 'pron_rel')
        self.assertEqual(p.lemma, None)
        self.assertEqual(p.pos, None)
        self.assertEqual(p.sense, None)
        p = Pred(string='abc_def_ghi_rel')
        self.assertEqual(p.type, Pred.GPRED)
        self.assertEqual(p.string, 'abc_def_ghi_rel')
        self.assertEqual(p.lemma, None)

    def testSpred(self):
        p = Pred('_dog_n_rel')
        self.assertEqual(p.type, Pred.SPRED)
        self.assertEqual(p.string, '_dog_n_rel')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, None)
        p = Pred('_犬_n_rel')
        self.assertEqual(p.type, Pred.SPRED)
        self.assertEqual(p.string, '_犬_n_rel')
        self.assertEqual(p.lemma, '犬')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, None)
        p = Pred('_dog_n_1_rel')
        self.assertEqual(p.type, Pred.SPRED)
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, '1')
        self.assertRaises(ValueError, Pred, '_dog_rel')
        self.assertRaises(ValueError, Pred, '_dog_n_1_2_rel')

    def testRealPred(self):
        p = Pred(lemma='dog', pos='n')
        self.assertEqual(p.type, Pred.REALPRED)
        self.assertEqual(p.string, '_dog_n_rel')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, None)
        p = Pred(lemma='犬', pos='n', sense='1')
        self.assertEqual(p.type, Pred.REALPRED)
        self.assertEqual(p.string, '_犬_n_1_rel')
        self.assertEqual(p.lemma, '犬')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, '1')
        p = Pred(lemma='dog', pos='n', sense=1) # sense is int, not str
        self.assertEqual(p.type, Pred.REALPRED)
        self.assertEqual(p.string, '_dog_n_1_rel')
        self.assertEqual(p.lemma, 'dog')
        self.assertEqual(p.pos, 'n')
        self.assertEqual(p.sense, '1')
        self.assertRaises(TypeError, Pred, lemma='dog')
        self.assertRaises(TypeError, Pred, pos='n')

    def testRelString(self):
        self.assertRaises(ValueError, Pred, string='_dog_n_1')
        p = Pred('"_dog_n_1_rel"')
        self.assertEqual(p.string, '"_dog_n_1_rel"')

    def testEq(self):
        self.assertEqual(Pred('_dog_n_rel'), Pred(lemma='dog', pos='n'))
        self.assertEqual(Pred('_dog_n_rel'), '_dog_n_rel')
        self.assertEqual('_dog_n_rel', Pred(lemma='dog', pos='n'))
        self.assertEqual(Pred('"_dog_n_rel"'), Pred("'_dog_n_rel'"))
        self.assertEqual(Pred('pron_rel'), 'pron_rel')
        self.assertNotEqual(Pred('_dog_n_rel'), Pred('dog_n_rel'))

class TestElementaryPredication(unittest.TestCase):
    def setUp(self):
        pass

class TestMrs(unittest.TestCase):
    def setUp(self):
        self.empty = mrs.Mrs()
        #self.basic = mrs.Mrs(ltop='h1', index='e2',
        #                     rels=[mrs.ElementaryPredicatation(pred=
