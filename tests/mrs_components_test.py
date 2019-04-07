# -*- coding: utf-8 -*-

import pytest

from delphin.exceptions import XmrsError
from delphin import predicate
from delphin.mrs.components import (
    sort_vid_split, var_sort, var_id, _VarGenerator,
    Lnk, _LnkMixin,
    Link, links, HandleConstraint, hcons,
    Node, ElementaryPredication as EP
)

from delphin.mrs.xmrs import Xmrs
from delphin.mrs.config import (
    CVARSORT, IVARG_ROLE, CONSTARG_ROLE, RSTR_ROLE,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST,
    LTOP_NODEID, FIRST_NODEID, BARE_EQ_ROLE
)


# store some example MRSs for later tests (note, some are made by hand)
# just a verb; e.g. "it rains"
x1 = Xmrs(
    top='h0',
    eps=[EP(10000, '_rain_v_1_rel', 'h1', {'ARG0': 'e2'})],
    hcons=[('h0', 'qeq', 'h1')]
)
# modified verb, e.g. "it rains heavily"
x2 = Xmrs(
    top='h0',
    eps=[
        EP(10000, '_rain_v_1_rel', 'h1', {'ARG0': 'e2'}),
        EP(10001, '_heavy_a_1_rel', 'h1',
           {'ARG0': 'e4', 'ARG1': 'e2'})
    ],
    hcons=[('h0', 'qeq', 'h1')]
)
# Verb and noun with quantifier; e.g. "the dog barks"
x3 = Xmrs(
    top='h0',
    eps=[
        EP(10000, '_bark_v_1_rel', 'h1',
           {'ARG0': 'e2', 'ARG1': 'x4'}),
        EP(10001, '_dog_n_1_rel', 'h3', {'ARG0': 'x4'}),
        EP(10002, 'the_q_rel', 'h5',
           {'ARG0': 'x4', 'RSTR': 'h6'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h6', 'qeq', 'h3')]
)
# label equality; e.g. "raining happens" (TODO: find better example)
x4 = Xmrs(
    top='h0',
    eps=[
        EP(10000, 'udef_q_rel', 'h4', {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, '_rain_v_1_rel', 'h7', {'ARG0': 'e8'}),
        EP(10002, 'nominalizationl_rel', 'h9',
           {'ARG0': 'x3', 'ARG1': 'h7'}),
        EP(10003, '_happen_v_1_rel', 'h1',
           {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h9')]
)
# undirected EQs; "the dog whose tail wagged barked"
x5 = Xmrs(
    top='h0',
    eps=[
        EP(10000, '_the_q_rel', 'h4',
           {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, '"_dog_n_1_rel"', 'h7', {'ARG0': 'x3'}),
        EP(10002, 'def_explicit_q_rel', 'h8',
              {'ARG0': 'x9', 'RSTR': 'h10'}),
        EP(10003, 'poss_rel', 'h7',
              {'ARG0': 'e12', 'ARG1': 'x9', 'ARG2': 'x3'}),
        EP(10004, '"_tail_n_1_rel"', 'h13', {'ARG0': 'x9'}),
        EP(10005, '"_wag_v_1_rel"', 'h7',
              {'ARG0': 'e14', 'ARG1': 'x9'}),
        EP(10006, '"_bark_v_1_rel"', 'h1',
              {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h7'),
           ('h10', 'qeq', 'h13')]
)
# ARG/NEQ from modifiers; "The big and scary dog barked."
x6 = Xmrs(
    top='h0',
    eps=[
        EP(10000, '_the_q_rel', 'h4',
           {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, '"_big_a_1_rel"', 'h7',
           {'ARG0': 'e8', 'ARG1': 'x3'}),
        EP(10002, '_and_c_rel', 'h9',
           {'ARG0': 'e10', 'L-INDEX': 'e8', 'R-INDEX': 'e11',
            'L-HNDL': 'h7', 'R-HNDL': 'h12'}),
        EP(10003, '"_scary_a_for_rel"', 'h12',
           {'ARG0': 'e11', 'ARG1': 'x3'}),
        EP(10004, '"_dog_n_1_rel"', 'h9', {'ARG0': 'x3'}),
        EP(10005, '"_bark_v_1_rel"', 'h1',
              {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h9')]
)

def test_sort_vid_split():
    assert sort_vid_split('x1') == ('x', '1')
    assert sort_vid_split('event10') == ('event', '10')
    assert sort_vid_split('ref-ind2') == ('ref-ind', '2')
    with pytest.raises(ValueError): sort_vid_split('x')
    with pytest.raises(ValueError): sort_vid_split('1')
    with pytest.raises(ValueError): sort_vid_split('1x')


def test_var_sort():
    assert var_sort('x1') == 'x'
    assert var_sort('event10') == 'event'
    assert var_sort('ref-ind2') == 'ref-ind'
    with pytest.raises(ValueError): var_sort('x')


def test_var_id():
    assert var_id('x1') == 1
    assert var_id('event10') == 10
    assert var_id('ref-ind2') == 2
    with pytest.raises(ValueError): var_id('1')


class TestVarGenerator():
    def test_init(self):
        vg = _VarGenerator()
        assert vg.vid == 1
        assert len(vg.store) == 0
        vg = _VarGenerator(starting_vid=5)
        assert vg.vid == 5
        assert len(vg.store) == 0

    def test_new(self):
        vg = _VarGenerator()
        v, vps = vg.new('x')
        assert v == 'x1'
        assert vg.vid == 2
        assert len(vg.store['x1']) == len(vps) == 0
        v, vps = vg.new('e', [('PROP', 'VAL')])
        assert v == 'e2'
        assert vg.vid == 3
        assert len(vg.store['e2']) == len(vps) == 1


class TestLnk():
    def test_raw_init(self):
        # don't allow just any Lnk type
        with pytest.raises(XmrsError): Lnk('lnktype', (0, 1))

    def testCharSpanLnk(self):
        lnk = Lnk.charspan(0, 1)
        assert lnk.type == Lnk.CHARSPAN
        assert lnk.data == (0, 1)
        assert str(lnk) == '<0:1>'
        repr(lnk)  # no error
        lnk = Lnk.charspan('0', '1')
        assert lnk.data == (0, 1)
        with pytest.raises(TypeError): Lnk.charspan(1)
        with pytest.raises(TypeError): Lnk.charspan([1, 2])
        with pytest.raises(TypeError): Lnk.charspan(1, 2, 3)
        with pytest.raises(ValueError): Lnk.charspan('a', 'b')

    def testChartSpanLnk(self):
        lnk = Lnk.chartspan(0, 1)
        assert lnk.type == Lnk.CHARTSPAN
        assert lnk.data == (0, 1)
        assert str(lnk) == '<0#1>'
        repr(lnk)  # no error
        lnk = Lnk.chartspan('0', '1')
        assert lnk.data == (0, 1)
        with pytest.raises(TypeError): Lnk.chartspan(1)
        with pytest.raises(TypeError): Lnk.chartspan([1, 2])
        with pytest.raises(TypeError): Lnk.chartspan(1, 2, 3)
        with pytest.raises(ValueError): Lnk.chartspan('a', 'b')

    def testTokensLnk(self):
        lnk = Lnk.tokens([1, 2, 3])
        assert lnk.type == Lnk.TOKENS
        assert lnk.data == (1, 2, 3)
        assert str(lnk) == '<1 2 3>'
        repr(lnk)  # no error
        lnk = Lnk.tokens(['1'])
        assert lnk.data == (1,)
        # empty tokens list might be invalid, but accept for now
        lnk = Lnk.tokens([])
        assert lnk.data == tuple()
        with pytest.raises(TypeError): Lnk.tokens(1)
        with pytest.raises(ValueError): Lnk.tokens(['a','b'])

    def testEdgeLnk(self):
        lnk = Lnk.edge(1)
        assert lnk.type == Lnk.EDGE
        assert lnk.data == 1
        assert str(lnk) == '<@1>'
        repr(lnk)  # no error
        lnk = Lnk.edge('1')
        assert lnk.data == 1
        with pytest.raises(TypeError): Lnk.edge(None)
        with pytest.raises(TypeError): Lnk.edge((1,))
        with pytest.raises(ValueError): Lnk.edge('a')


class TestLnkMixin():
    def test_inherit(self):
        class NoLnk(_LnkMixin):
            pass
        n = NoLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithNoneLnk(_LnkMixin):
            def __init__(self):
                self.lnk = None
        n = WithNoneLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithNonCharspanLnk(_LnkMixin):
            def __init__(self):
                self.lnk = Lnk.chartspan(0,1)
        n = WithNonCharspanLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithCharspanLnk(_LnkMixin):
            def __init__(self):
                self.lnk = Lnk.charspan(0,1)
        n = WithCharspanLnk()
        assert n.cfrom == 0


class TestLink():
    def test_construct(self):
        with pytest.raises(TypeError): Link()
        with pytest.raises(TypeError): Link(0)
        with pytest.raises(TypeError): Link(0, 1)
        with pytest.raises(TypeError): Link(0, 1, 'rargname')
        l = Link(0, 1, 'ARG', 'NEQ')
        assert l.start == 0
        assert l.end == 1
        assert l.rargname == 'ARG'
        assert l.post == 'NEQ'
        repr(l)  # no error


def test_links():
    assert list(links(x1)) == [(0, 10000, None, 'H')]
    assert sorted(links(x2)) == [
        (0, 10000, None, 'H'), (10001, 10000, 'ARG1', 'EQ')
    ]
    assert sorted(links(x3)) == [
        (0, 10000, None, 'H'),
        (10000, 10001, 'ARG1', 'NEQ'),
        (10002, 10001, 'RSTR', 'H')
    ]
    assert sorted(links(x4)) == [
        (0, 10003, None, 'H'),
        (10000, 10002, 'RSTR', 'H'),
        (10002, 10001, 'ARG1', 'HEQ'),
        (10003, 10002, 'ARG1', 'NEQ')
    ]
    assert sorted(links(x5)) == [
        (0, 10006, None, 'H'),
        (10000, 10001, 'RSTR', 'H'),
        (10002, 10004, 'RSTR', 'H'),
        (10003, 10001, 'ARG2', 'EQ'),
        (10003, 10004, 'ARG1', 'NEQ'),
        (10005, 10001, BARE_EQ_ROLE, 'EQ'),
        (10005, 10004, 'ARG1', 'NEQ'),
        (10006, 10001, 'ARG1', 'NEQ')
    ]
    assert sorted(links(x6)) == [
        (0, 10005, None, 'H'),
        (10000, 10004, 'RSTR', 'H'),
        (10001, 10004, 'ARG1', 'NEQ'),
        (10002, 10001, 'L-HNDL', 'HEQ'),
        (10002, 10001, 'L-INDEX', 'NEQ'),
        (10002, 10003, 'R-HNDL', 'HEQ'),
        (10002, 10003, 'R-INDEX', 'NEQ'),
        (10002, 10004, BARE_EQ_ROLE, 'EQ'),
        (10003, 10004, 'ARG1', 'NEQ'),
        (10005, 10004, 'ARG1', 'NEQ')
    ]


class TestHandleConstraint():
    def test_construct(self):
        h1 = 'handle1'
        h2 = 'handle2'
        with pytest.raises(TypeError): HandleConstraint()
        with pytest.raises(TypeError): HandleConstraint(h1)
        with pytest.raises(TypeError): HandleConstraint(h1, HandleConstraint.QEQ)
        hc = HandleConstraint(h1, HandleConstraint.QEQ, h2)
        assert hc.hi == h1
        assert hc.relation == HandleConstraint.QEQ
        assert hc.lo == h2
        hc = HandleConstraint(h1, HandleConstraint.LHEQ, h2)
        assert hc.relation == HandleConstraint.LHEQ
        hc = HandleConstraint('h1', HandleConstraint.QEQ, 'h2')
        assert hc.hi == 'h1'
        assert hc.lo == 'h2'
        repr(hc)  # no error

    def test_qeq(self):
        # qeq classmethod is just a convenience
        hc = HandleConstraint.qeq('h0', 'h1')
        assert hc.hi == 'h0'
        assert hc.relation == HandleConstraint.QEQ
        assert hc.lo == 'h1'

    def test_equality(self):
        h1 = 'h1'
        h2 = 'h2'
        hc1 = HandleConstraint(h1, HandleConstraint.QEQ, h2)
        assert hc1 == HandleConstraint(h1, HandleConstraint.QEQ, h2)
        assert hc1 != HandleConstraint(h2, HandleConstraint.QEQ, h1)
        assert hc1 != HandleConstraint(h1, HandleConstraint.LHEQ, h2)

    def test_hashable(self):
        hc1 = HandleConstraint('h1', HandleConstraint.QEQ, 'h2')
        hc2 = HandleConstraint('h3', HandleConstraint.QEQ, 'h4')
        d = {hc1:1, hc2:2}
        assert d[hc1] == 1
        assert d[hc2] == 2


def test_hcons():
    assert sorted(hcons(x1)) == [('h0', 'qeq', 'h1')]
    assert sorted(hcons(x2)) == [('h0', 'qeq', 'h1')]
    assert sorted(hcons(x3)) == [('h0', 'qeq', 'h1'), ('h6', 'qeq', 'h3')]
    assert sorted(hcons(x4)) == [('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h9')]
    assert sorted(hcons(x5)) == [('h0', 'qeq', 'h1'), ('h10', 'qeq', 'h13'),
                                 ('h5', 'qeq', 'h7')]


class TestNode():
    def test_construct(self):
        # minimum is a nodeid and a pred
        with pytest.raises(TypeError): Node()
        with pytest.raises(TypeError): Node(10000)
        n = Node(10000, '_dog_n_rel')
        assert n.nodeid == 10000
        assert n.pred == '_dog_n_rel'

    def test_sortinfo(self):
        n = Node(10000, '_dog_n_rel')
        assert len(n.sortinfo) == 0
        n = Node(10000, '_dog_n_rel',
                 sortinfo=[(CVARSORT, 'x')])
        assert len(n.sortinfo) == 1
        n = Node(10000, '_dog_n_rel',
                 sortinfo=[(CVARSORT, 'x'), ('PER', '3')])
        assert len(n.sortinfo) == 2
        n2 = Node(10001, '_cat_n_rel',
                  sortinfo=dict([(CVARSORT,'x'), ('PER','3')]))
        assert n.sortinfo == n2.sortinfo

    def test_properties(self):
        n = Node(10000, '_dog_n_rel')
        assert len(n.properties) == 0
        n = Node(10000, '_dog_n_rel',
                 sortinfo=[(CVARSORT, 'x')])
        assert len(n.properties) == 0
        n = Node(10000, '_dog_n_rel',
                 sortinfo=[(CVARSORT, 'x'), ('PER', '3')])
        assert len(n.properties) == 1
        n2 = Node(10001, '_cat_n_rel',
                  sortinfo=dict([(CVARSORT,'x'), ('PER','3')]))
        assert n.properties == n2.properties

    def test_lnk(self):
        n = Node(10000, '_dog_n_rel')
        assert n.lnk == None
        assert n.cfrom == -1
        assert n.cto == -1
        n = Node(10000, '_dog_n_rel',
                 lnk=Lnk.charspan(0,1))
        assert n.lnk == Lnk.charspan(0,1)
        assert n.cfrom == 0
        assert n.cto == 1

    def test_cvarsort(self):
        n = Node(10000, '_dog_n_rel')
        assert n.cvarsort == None
        n.cvarsort = 'x'
        assert n.cvarsort == 'x'
        assert n.sortinfo == dict([(CVARSORT, 'x')])
        n = Node(10000, '_run_v_rel',
                 sortinfo=dict([(CVARSORT, 'e')]))
        assert n.cvarsort == 'e'


class TestElementaryPredication():
    def test_construct(self):
        with pytest.raises(TypeError): EP()
        with pytest.raises(TypeError): EP(10)
        with pytest.raises(TypeError): EP(10, '_dog_n_rel')
        e = EP(10, '_dog_n_rel', 'h1')
        assert e.nodeid == 10
        assert e.pred == '_dog_n_rel'
        assert e.label == 'h1'

    def test_args(self):
        p = '_chase_v_rel'
        lbl = 'h1'
        e = EP(11, p, lbl)
        assert len(e.args) == 0
        v1 = 'e2'
        e = EP(11, p, lbl, args={IVARG_ROLE: v1})
        assert len(e.args) == 1
        assert e.args[IVARG_ROLE] == v1
        v2 = 'x3'
        e = EP(11, p, lbl, args={IVARG_ROLE: v1, 'ARG1': v2})
        assert len(e.args) == 2
        assert e.args[IVARG_ROLE] == v1
        assert e.args['ARG1'] == v2

    def test_is_quantifier(self):
        e = EP(10, '_the_q_rel', 'h1', args={RSTR_ROLE: 'h2'})
        assert e.is_quantifier() == True
        # not a q pred, but has RSTR
        e = EP(10, '_dog_n_rel', 'h1', args={RSTR_ROLE: 'h2'})
        assert e.is_quantifier() == True
        # a q pred, but no RSTR
        e = EP(10, '_the_q_rel', 'h1', args={})
        assert e.is_quantifier() == False
