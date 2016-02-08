# -*- coding: UTF-8 -*-

import pytest

from delphin._exceptions import XmrsError
from delphin.mrs.components import (
    sort_vid_split, var_sort, var_id, VarGenerator,
    Lnk, LnkMixin,
    Link, links, HandleConstraint, hcons,
    Pred, split_pred_string, is_valid_pred_string, normalize_pred_string,
    Node, ElementaryPredication as EP
)
spred = Pred.stringpred
from delphin.mrs.xmrs import Xmrs
from delphin.mrs.config import (
    CVARSORT, IVARG_ROLE, CONSTARG_ROLE, RSTR_ROLE,
    EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST,
    LTOP_NODEID, FIRST_NODEID
)


# store some example MRSs for later tests (note, some are made by hand)
# just a verb; e.g. "it rains"
x1 = Xmrs(
    top='h0',
    eps=[EP(10000, spred('_rain_v_1_rel'), 'h1', {'ARG0': 'e2'})],
    hcons=[('h0', 'qeq', 'h1')]
)
# modified verb, e.g. "it rains heavily"
x2 = Xmrs(
    top='h0',
    eps=[
        EP(10000, spred('_rain_v_1_rel'), 'h1', {'ARG0': 'e2'}),
        EP(10001, spred('_heavy_a_1_rel'), 'h1',
           {'ARG0': 'e4', 'ARG1': 'e2'})
    ],
    hcons=[('h0', 'qeq', 'h1')]
)
# Verb and noun with quantifier; e.g. "the dog barks"
x3 = Xmrs(
    top='h0',
    eps=[
        EP(10000, spred('_bark_v_1_rel'), 'h1',
           {'ARG0': 'e2', 'ARG1': 'x4'}),
        EP(10001, spred('_dog_n_1_rel'), 'h3', {'ARG0': 'x4'}),
        EP(10002, spred('the_q_rel'), 'h5',
           {'ARG0': 'x4', 'RSTR': 'h6'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h6', 'qeq', 'h3')]
)
# label equality; e.g. "raining happens" (TODO: find better example)
x4 = Xmrs(
    top='h0',
    eps=[
        EP(10000, spred('udef_q_rel'), 'h4', {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, spred('_rain_v_1_rel'), 'h7', {'ARG0': 'e8'}),
        EP(10002, spred('nominalizationl_rel'), 'h9',
           {'ARG0': 'x3', 'ARG1': 'h7'}),
        EP(10003, spred('_happen_v_1_rel'), 'h1',
           {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h9')]
)
# undirected EQs; "the dog whose tail wagged barked"
x5 = Xmrs(
    top='h0',
    eps=[
        EP(10000, spred('_the_q_rel'), 'h4',
           {'ARG0': 'x3', 'RSTR': 'h5'}),
        EP(10001, spred('"_dog_n_1_rel"'), 'h7', {'ARG0': 'x3'}),
        EP(10002, spred('def_explicit_q_rel'), 'h8',
              {'ARG0': 'x9', 'RSTR': 'h10'}),
        EP(10003, spred('poss_rel'), 'h7',
              {'ARG0': 'e12', 'ARG1': 'x9', 'ARG2': 'x3'}),
        EP(10004, spred('"_tail_n_1_rel"'), 'h13', {'ARG0': 'x9'}),
        EP(10005, spred('"_wag_v_1_rel"'), 'h7',
              {'ARG0': 'e14', 'ARG1': 'x9'}),
        EP(10006, spred('"_bark_v_1_rel"'), 'h1',
              {'ARG0': 'e2', 'ARG1': 'x3'})
    ],
    hcons=[('h0', 'qeq', 'h1'), ('h5', 'qeq', 'h7'),
           ('h10', 'qeq', 'h13')]
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
        vg = VarGenerator()
        assert vg.vid == 1
        assert len(vg.store) == 0
        vg = VarGenerator(starting_vid=5)
        assert vg.vid == 5
        assert len(vg.store) == 0

    def test_new(self):
        vg = VarGenerator()
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
        (10001, 10005, None, 'EQ'),
        (10002, 10004, 'RSTR', 'H'),
        (10003, 10001, 'ARG2', 'EQ'),
        (10003, 10004, 'ARG1', 'NEQ'),
        (10005, 10004, 'ARG1', 'NEQ'),
        (10006, 10001, 'ARG1', 'NEQ')
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


class TestPred():
    def testGpred(self):
        p = Pred.grammarpred('pron_rel')
        assert p.type == Pred.GRAMMARPRED
        assert p.string == 'pron_rel'
        assert p.lemma == 'pron'
        assert p.pos == None
        assert p.sense == None
        assert p.short_form() == 'pron'
        p = Pred.grammarpred('udef_q_rel')
        assert p.string == 'udef_q_rel'
        assert p.lemma == 'udef'
        assert p.pos == 'q'
        assert p.sense == None
        assert p.short_form() == 'udef_q'
        p = Pred.grammarpred('abc_def_ghi_rel')
        assert p.type == Pred.GRAMMARPRED
        assert p.string == 'abc_def_ghi_rel'
        # pos must be a single character, so we get abc_def, ghi, rel
        assert p.lemma == 'abc_def'
        assert p.pos == None
        assert p.sense == 'ghi'
        assert p.short_form() == 'abc_def_ghi'
        repr(p)  # no error

    def testSpred(self):
        p = spred('_dog_n_rel')
        assert p.type == Pred.STRINGPRED
        assert p.string == '_dog_n_rel'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == None
        assert p.short_form() == '_dog_n'
        p = spred('_犬_n_rel')
        assert p.type == Pred.STRINGPRED
        assert p.string == '_犬_n_rel'
        assert p.lemma == '犬'
        assert p.pos == 'n'
        assert p.sense == None
        assert p.short_form() == '_犬_n'
        p = spred('"_dog_n_1_rel"')
        assert p.type == Pred.STRINGPRED
        assert p.string == '"_dog_n_1_rel"'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == '1'
        assert p.short_form() == '_dog_n_1'
        #TODO: the following shouldn't throw warnings.. the code should
        # be more robust, but there should be some Warning or logging
        #with pytest.raises(ValueError): spred('_dog_rel')
        #with pytest.raises(ValueError): spred('_dog_n_1_2_rel')
        repr(p)  # no error

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
        assert p.short_form() == '_dog_n'
        # try with arg names, unicode, and sense
        p = Pred.realpred(lemma='犬', pos='n', sense='1')
        assert p.type == Pred.REALPRED
        assert p.string == '_犬_n_1_rel'
        assert p.lemma == '犬'
        assert p.pos == 'n'
        assert p.sense == '1'
        assert p.short_form() == '_犬_n_1'
        # in case sense is int, not str
        p = Pred.realpred('dog', 'n', 1)
        assert p.type == Pred.REALPRED
        assert p.string == '_dog_n_1_rel'
        assert p.lemma == 'dog'
        assert p.pos == 'n'
        assert p.sense == '1'
        assert p.short_form() == '_dog_n_1'
        with pytest.raises(TypeError): Pred.realpred(lemma='dog')
        with pytest.raises(TypeError): Pred.realpred(pos='n')
        repr(p)  # no error

    def testEq(self):
        assert spred('_dog_n_rel') == Pred.realpred(lemma='dog', pos='n')
        assert spred('_dog_n_rel') == '_dog_n_rel'
        assert '_dog_n_rel' == Pred.realpred(lemma='dog', pos='n')
        assert spred('"_dog_n_rel"') == spred("'_dog_n_rel")
        assert Pred.grammarpred('pron_rel') == 'pron_rel'
        assert Pred.string_or_grammar_pred('_dog_n_rel') != Pred.string_or_grammar_pred('dog_n_rel')
        assert (spred('_dog_n_rel') == None) == False
        assert spred('_dog_n_1_rel') == spred('_Dog_N_1_rel')

    def test_is_quantifier(self):
        assert spred('"_the_q_rel"').is_quantifier() == True
        assert spred('_udef_q_rel').is_quantifier() == True
        # how do we do this one?
        # assert spred('quant_rel').is_quantifier() == True
        assert spred('abstract_q_rel').is_quantifier() == True
        assert spred('_the_q').is_quantifier() == True
        assert spred('"_the_q"').is_quantifier() == True
        assert spred('_q_n_letter_rel').is_quantifier() == False



def test_split_pred_string():
    sps = split_pred_string
    # with rel
    assert sps('pron_rel') == ('pron', None, None, 'rel')
    # with pos
    assert sps('udef_q_rel') == ('udef', 'q', None, 'rel')
    # with sense (and quotes)
    assert sps('"_bark_v_1_rel"') == ('bark', 'v', '1', 'rel')
    # some odd variations (some are not strictly well-formed)
    assert sps('coord') == ('coord', None, None, None)
    assert sps('some_relation') == ('some', None, 'relation', None)
    assert sps('_24/7_a_1_rel') == ('24/7', 'a', '1', 'rel')
    assert sps('_a+bit_q_rel') == ('a+bit', 'q', None, 'rel')
    assert sps('_A$_n_1_rel') == ('A$', 'n', '1', 'rel')
    assert sps('_only_child_n_1_rel') == ('only_child', 'n', '1', 'rel')


def test_is_valid_pred_string():
    ivps = is_valid_pred_string
    # valid
    assert ivps('pron_rel')
    assert ivps('\'pron_rel')  # single open qoute
    assert ivps('"pron_rel"')  # surrounding double-quotes
    assert ivps('udef_q_rel')
    assert ivps('"_dog_n_1_rel"')
    assert ivps('"_ad+hoc_a_1_rel"')
    assert ivps('"_look_v_up-at_rel"')
    assert ivps('_24/7_a_1_rel')
    assert ivps('_a+bit_q_rel')
    assert ivps('_A$_n_1_rel')
    # invalid
    assert not ivps('coord')
    assert not ivps('coord_relation')
    assert not ivps('_only_child_n_1_rel')


def test_normalize_pred_string():
    nps = normalize_pred_string
    assert nps('pron') == 'pron_rel'
    assert nps('"udef_q_rel"') == 'udef_q_rel'
    assert nps('\'udef_q_rel') == 'udef_q_rel'
    assert nps('_dog_n_1_rel') == '_dog_n_1_rel'

class TestNode():
    def test_construct(self):
        # minimum is a nodeid and a pred
        with pytest.raises(TypeError): Node()
        with pytest.raises(TypeError): Node(10000)
        n = Node(10000, spred('_dog_n_rel'))
        assert n.nodeid == 10000
        assert n.pred == '_dog_n_rel'

    def test_sortinfo(self):
        n = Node(10000, spred('_dog_n_rel'))
        assert len(n.sortinfo) == 0
        n = Node(10000, spred('_dog_n_rel'),
                 sortinfo=[(CVARSORT, 'x')])
        assert len(n.sortinfo) == 1
        n = Node(10000, spred('_dog_n_rel'),
                 sortinfo=[(CVARSORT, 'x'), ('PER', '3')])
        assert len(n.sortinfo) == 2
        n2 = Node(10001, spred('_cat_n_rel'),
                  sortinfo=dict([(CVARSORT,'x'), ('PER','3')]))
        assert n.sortinfo == n2.sortinfo

    def test_lnk(self):
        n = Node(10000, spred('_dog_n_rel'))
        assert n.lnk == None
        assert n.cfrom == -1
        assert n.cto == -1
        n = Node(10000, spred('_dog_n_rel'),
                 lnk=Lnk.charspan(0,1))
        assert n.lnk == Lnk.charspan(0,1)
        assert n.cfrom == 0
        assert n.cto == 1

    def test_cvarsort(self):
        n = Node(10000, spred('_dog_n_rel'))
        assert n.cvarsort == None
        n.cvarsort = 'x'
        assert n.cvarsort == 'x'
        assert n.sortinfo == dict([(CVARSORT, 'x')])
        n = Node(10000, spred('_run_v_rel'),
                 sortinfo=dict([(CVARSORT, 'e')]))
        assert n.cvarsort == 'e'


class TestElementaryPredication():
    def test_construct(self):
        with pytest.raises(TypeError): EP()
        with pytest.raises(TypeError): EP(10)
        with pytest.raises(TypeError): EP(10, spred('_dog_n_rel'))
        e = EP(10, spred('_dog_n_rel'), 'h1')
        assert e.nodeid == 10
        assert e.pred == '_dog_n_rel'
        assert e.label == 'h1'

    def test_args(self):
        p = spred('_chase_v_rel')
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
        e = EP(10, spred('_the_q_rel'), 'h1', args={RSTR_ROLE: 'h2'})
        assert e.is_quantifier() == True
        # not a q pred, but has RSTR
        e = EP(10, spred('_dog_n_rel'), 'h1', args={RSTR_ROLE: 'h2'})
        assert e.is_quantifier() == True
        # a q pred, but no RSTR
        e = EP(10, spred('_the_q_rel'), 'h1', args={})
        assert e.is_quantifier() == False
