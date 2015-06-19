# -*- coding: UTF-8 -*-

import pytest

from delphin.mrs.components import (
    sort_vid_split, var_sort, var_id,
    Lnk, LnkMixin,
    Link, HandleConstraint,
    Pred, Node, ElementaryPredication as EP
)
from delphin.mrs.config import (
    CVARSORT, IVARG_ROLE, CONSTARG_ROLE,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST,
    LTOP_NODEID, FIRST_NODEID
)


def test_sort_vid_split():
    assert sort_vid_split('x1') == ('x', '1')
    assert sort_vid_split('event10') == ('event', '10')
    with pytest.raises(ValueError): sort_vid_split('x')
    with pytest.raises(ValueError): sort_vid_split('1')
    with pytest.raises(ValueError): sort_vid_split('1x')


def test_var_sort():
    assert var_sort('x1') == 'x'
    assert var_sort('event10') == 'event'
    with pytest.raises(ValueError): var_sort('x')


def test_var_id():
    assert var_id('x1') == 1
    assert var_id('event10') == 10
    with pytest.raises(ValueError): var_id('1')


class TestLnk():
    def test_raw_init(self):
        lnk = Lnk('lnktype', (0, 1))
        assert lnk.type == 'lnktype'
        assert lnk.data == (0, 1)

    def testCharSpanLnk(self):
        lnk = Lnk.charspan(0, 1)
        assert lnk.type == Lnk.CHARSPAN
        assert lnk.data == (0, 1)
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
        lnk = Lnk.edge('1')
        assert lnk.data == 1
        with pytest.raises(TypeError): Lnk.edge(None)
        with pytest.raises(TypeError): Lnk.edge((1,))
        with pytest.raises(ValueError): Lnk.edge('a')


class TestLnkMixin():
    def test_inherit(self):
        class NoLnk(LnkMixin):
            pass
        n = NoLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithNoneLnk(LnkMixin):
            def __init__(self):
                self.lnk = None
        n = WithNoneLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithNonCharspanLnk(LnkMixin):
            def __init__(self):
                self.lnk = Lnk.chartspan(0,1)
        n = WithNonCharspanLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithCharspanLnk(LnkMixin):
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


class TestPred():
    def testGpred(self):
        p = Pred.grammarpred('pron_rel')
        assert p.type == Pred.GRAMMARPRED
        assert p.string == 'pron_rel'
        assert p.lemma == 'pron'
        assert p.pos == None
        assert p.sense == None
        p = Pred.grammarpred('udef_q_rel')
        assert p.string == 'udef_q_rel'
        assert p.lemma == 'udef'
        assert p.pos == 'q'
        assert p.sense == None
        p = Pred.grammarpred('abc_def_ghi_rel')
        assert p.type == Pred.GRAMMARPRED
        assert p.string == 'abc_def_ghi_rel'
        # pos must be a single character, so we get abc_def, ghi, rel
        assert p.lemma == 'abc_def'
        assert p.pos == None
        assert p.sense == 'ghi'

    def testSpred(self):
        p = Pred.stringpred('_dog_n_rel')
        assert p.type == Pred.STRINGPRED
        assert p.string == '_dog_n_rel'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == None
        p = Pred.stringpred('_犬_n_rel')
        assert p.type == Pred.STRINGPRED
        assert p.string == '_犬_n_rel'
        assert p.lemma == '犬'
        assert p.pos == 'n'
        assert p.sense == None
        p = Pred.stringpred('"_dog_n_1_rel"')
        assert p.type == Pred.STRINGPRED
        assert p.string == '"_dog_n_1_rel"'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == '1'
        #TODO: the following shouldn't throw warnings.. the code should
        # be more robust, but there should be some Warning or logging
        #with pytest.raises(ValueError): Pred.stringpred('_dog_rel')
        #with pytest.raises(ValueError): Pred.stringpred('_dog_n_1_2_rel')

    def testStringOrGrammarPred(self):
        p = Pred.string_or_grammar_pred('_dog_n_rel')
        assert p.type == Pred.STRINGPRED
        p = Pred.string_or_grammar_pred('pron_rel')
        assert p.type == Pred.GRAMMARPRED

    def testRealPred(self):
        # basic, no sense arg
        p = Pred.realpred('dog', 'n')
        assert p.type == Pred.REALPRED
        assert p.string == '_dog_n_rel'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == None
        # try with arg names, unicode, and sense
        p = Pred.realpred(lemma='犬', pos='n', sense='1')
        assert p.type == Pred.REALPRED
        assert p.string == '_犬_n_1_rel'
        assert p.lemma == '犬'
        assert p.pos == 'n'
        assert p.sense == '1'
        # in case sense is int, not str
        p = Pred.realpred('dog', 'n', 1)
        assert p.type == Pred.REALPRED
        assert p.string == '_dog_n_1_rel'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == '1'
        with pytest.raises(TypeError): Pred.realpred(lemma='dog')
        with pytest.raises(TypeError): Pred.realpred(pos='n')

    def testEq(self):
        assert Pred.stringpred('_dog_n_rel') == Pred.realpred(lemma='dog', pos='n')
        assert Pred.stringpred('_dog_n_rel') == '_dog_n_rel'
        assert '_dog_n_rel' == Pred.realpred(lemma='dog', pos='n')
        assert Pred.stringpred('"_dog_n_rel"') == Pred.stringpred("'_dog_n_rel")
        assert Pred.grammarpred('pron_rel') == 'pron_rel'
        assert Pred.string_or_grammar_pred('_dog_n_rel') != Pred.string_or_grammar_pred('dog_n_rel')


class TestNode():
    def test_construct(self):
        # minimum is a nodeid and a pred
        with pytest.raises(TypeError): Node()
        with pytest.raises(TypeError): Node(10000)
        n = Node(10000, Pred.stringpred('_dog_n_rel'))
        assert n.nodeid == 10000
        assert n.pred == '_dog_n_rel'

    def test_sortinfo(self):
        n = Node(10000, Pred.stringpred('_dog_n_rel'))
        assert len(n.sortinfo) == 0
        n = Node(10000, Pred.stringpred('_dog_n_rel'),
                 sortinfo=[(CVARSORT, 'x')])
        assert len(n.sortinfo) == 1
        n = Node(10000, Pred.stringpred('_dog_n_rel'),
                 sortinfo=[(CVARSORT, 'x'), ('PER', '3')])
        assert len(n.sortinfo) == 2
        n2 = Node(10001, Pred.stringpred('_cat_n_rel'),
                  sortinfo=dict([(CVARSORT,'x'), ('PER','3')]))
        assert n.sortinfo == n2.sortinfo

    def test_lnk(self):
        n = Node(10000, Pred.stringpred('_dog_n_rel'))
        assert n.lnk == None
        assert n.cfrom == -1
        assert n.cto == -1
        n = Node(10000, Pred.stringpred('_dog_n_rel'),
                 lnk=Lnk.charspan(0,1))
        assert n.lnk == Lnk.charspan(0,1)
        assert n.cfrom == 0
        assert n.cto == 1

    def test_cvarsort(self):
        n = Node(10000, Pred.stringpred('_dog_n_rel'))
        assert n.cvarsort == None
        n.cvarsort = 'x'
        assert n.cvarsort == 'x'
        assert n.sortinfo == dict([(CVARSORT, 'x')])
        n = Node(10000, Pred.stringpred('_run_v_rel'),
                 sortinfo=dict([(CVARSORT, 'e')]))
        assert n.cvarsort == 'e'


class TestElementaryPredication():
    def test_construct(self):
        with pytest.raises(TypeError): EP()
        with pytest.raises(TypeError): EP(10)
        with pytest.raises(TypeError): EP(10, Pred.stringpred('_dog_n_rel'))
        e = EP(10, Pred.stringpred('_dog_n_rel'), 'h1')
        assert e.nodeid == 10
        assert e.pred == '_dog_n_rel'
        assert e.label == 'h1'

    def test_args(self):
        p = Pred.stringpred('_chase_v_rel')
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
