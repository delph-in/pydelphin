# -*- coding: UTF-8 -*-
import unittest
from delphin.mrs.xmrs import (
    Xmrs, )
from delphin.mrs.components import (
    MrsVariable, AnchorMixin, Lnk, LnkMixin, Hook,
    Argument, Link, HandleConstraint,
    Pred, Node, ElementaryPredication as EP
)
from delphin.mrs.config import (
    QEQ, LHEQ, OUTSCOPES, CVARSORT, IVARG_ROLE, CONSTARG_ROLE,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST,
    LTOP_NODEID, FIRST_NODEID, ANCHOR_SORT,
)

class TestXmrs(unittest.TestCase):
    def test_empty(self):
        x = Xmrs()
        self.assertEqual((x.hook.top, x.hook.index, x.hook.xarg),
                         (None, None, None))
        self.assertEqual(x.ltop, None)
        self.assertEqual(x.top, None)
        self.assertEqual(x.index, None)
        self.assertEqual(x.nodeids, [])
        self.assertEqual(x.anchors, [])
        self.assertEqual(x.variables, [])
        self.assertEqual(x.introduced_variables, [])
        self.assertEqual(x.intrinsic_variables, [])
        self.assertEqual(x.bound_variables, [])
        self.assertEqual(x.labels, [])
        self.assertEqual(x.nodes, [])
        self.assertEqual(x.eps, [])
        self.assertEqual(x.args, [])
        self.assertEqual(x.hcons, [])
        self.assertEqual(x.icons, [])
        self.assertEqual(x.links, [])

#class TestXmrsLinks(unittest.TestCase):
#    def setUp(self):
#        ltop = MrsVariable(0,'h')
#        sleep_iv = MrsVariable(1,'e')
#        sleep_lbl = MrsVariable(2, 'h')
#        dog_lbl = MrsVariable(3, 'h')
#        dog_iv = MrsVariable(4, 'x')
#        a_lbl = MrsVariable(5, 'h')
#        a_hole = MrsVariable(6, 'h')
#        a_body = MrsVariable(7, 'h')
#        big_lbl = MrsVariable(8, 'h')
#        big_iv = MrsVariable(9, 'e')
#
#        self.xmrs = Xmrs(
#            hook=Hook(ltop=ltop,index=sleep_iv),
#            nodes=[Node(10000, Pred.stringpred('_a_q_rel')),
#                   Node(10001, Pred.stringpred('_big_a_1_rel')),
#                   Node(10002, Pred.stringpred('_dog_n_1_rel')),
#                   Node(10003, Pred.stringpred('_sleep_v_1_rel'))],
#            args=[Argument(10000, 'RSTR', a_hole),
#                  Argument(10000, 'BODY', a_body),
#                  Argument(10001, 'ARG1', dog_iv),
#                  Argument(10003, 'ARG1', dog_iv)],
#            hcons=[HandleConstraint(ltop, QEQ, sleep_lbl),
#                   HandleConstraint(a_hole, QEQ, dog_lbl)],
#            ivs=[(10000, dog_iv), (10001, big_iv), (10002, dog_iv),
#                 (10003, sleep_iv)],
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
