# -*- coding: UTF-8 -*-

import pytest

from delphin.mrs.components import Pred
from delphin.mrs.xmrs import Xmrs
from delphin.mrs import simplemrs  # for convenience in later tests
from delphin._exceptions import XmrsError

# simplemrs is only used for functions where large MRSs are needed and
# constructing them manually is cumbersome. Try to avoid using it for
# the basic Xmrs tests, because we must assume simplemrs is working as
# expected (make sure the simplemrs tests pass, too)
read = simplemrs.loads_one

class TestXmrs():
    def test_empty(self):
        x = Xmrs()
        assert x.top is None
        assert x.index is None
        assert x.xarg is None
        assert len(x.eps()) == 0
        assert len(x.hcons()) == 0
        assert len(x.icons()) == 0
        assert len(x.variables()) == 0

    def test_add_eps(self):
        x = Xmrs()
        # only nodeid
        with pytest.raises(XmrsError):
            x.add_eps([(10000,)])
        assert len(x.eps()) == 0
        # nodeid and pred
        with pytest.raises(XmrsError):
            x.add_eps([(10000, Pred.stringpred('_v_v_rel'))])
        assert len(x.eps()) == 0
        # nodeid, pred, and label
        with pytest.raises(XmrsError):
            x.add_eps([(10000, Pred.stringpred('_v_v_rel'), 'h1')])
        assert len(x.eps()) == 0

        # nodeid, pred, label, and argdict (the minimum)
        x.add_eps([(10000, Pred.stringpred('_v_v_rel'), 'h1', {})])
        # make sure it was entered correctly and is unchanged
        assert len(x.eps()) == 1
        assert x.eps()[0][0] == 10000
        ep = x.ep(10000)
        assert ep[0] == 10000
        assert isinstance(ep[1], Pred) and ep[1].string == '_v_v_rel'
        assert ep[2] == 'h1'
        assert ep[3] == {}

        # cannot have more than one ep with the same nodeid
        with pytest.raises(XmrsError):
            x.add_eps([(10000, Pred.stringpred('_n_n_rel'), 'h3', {})])
        assert len(x.eps()) == 1

    def test_add_hcons(self):
        x = Xmrs()
        # only hi
        with pytest.raises(XmrsError):
            x.add_hcons([('h0')])
        # only hi and relation
        with pytest.raises(XmrsError):
            x.add_hcons([('h0', 'qeq')])
        # hi, relation, and lo (the minimum, but probably max, too)
        x.add_hcons([('h0', 'qeq', 'h1')])
        assert len(x.hcons()) == 1
        hc = x.hcon('h0')
        assert hc[0] == 'h0'
        assert hc[1] == 'qeq'
        assert hc[2] == 'h1'

        # cannot have more than one hcons with the same hi variable
        with pytest.raises(XmrsError):
            x.add_hcons([('h0', 'qeq', 'h2')])
        assert len(x.hcons()) == 1

    def test_add_icons(self):
        x = Xmrs()
        # only hi
        with pytest.raises(XmrsError):
            x.add_icons([('x0')])
        # only hi and relation
        with pytest.raises(XmrsError):
            x.add_icons([('x0', 'topic')])
        # hi, relation, and lo (the minimum, but probably max, too)
        x.add_icons([('x0', 'topic', 'x1')])
        assert len(x.icons()) == 1
        ics = x.icons('x0')
        assert len(ics) == 1
        assert ics[0][0] == 'x0'
        assert ics[0][1] == 'topic'
        assert ics[0][2] == 'x1'

        # can have more than one icons with the same left variable
        x.add_icons([('x0', 'focus', 'x2')])
        assert len(x.icons()) == 2

    def test_top(self):
        x = Xmrs(top='h0')
        assert x.top == 'h0'
        assert x.ltop == 'h0'  # currently just a synonym for top

    def test_index(self):
        x = Xmrs(index='e0')
        assert x.index == 'e0'

    def test_xarg(self):
        x = Xmrs(xarg='e0')
        assert x.xarg == 'e0'

    def test_eps(self):
        x = Xmrs()
        sp = Pred.stringpred
        assert len(x.eps()) == 0
        x.add_eps([(10, sp('_n_n_rel'), 'h3', {'ARG0': 'x4'})])
        assert len(x.eps()) == 1
        assert x.eps()[0][0] == 10
        assert x.eps()[0][1] == sp('_n_n_rel')
        assert x.eps()[0][2] == 'h3'
        assert x.eps()[0][3] == {'ARG0': 'x4'}
        x.add_eps([
            (11, sp('_q_q_rel'), 'h5', {'ARG0': 'x4', 'RSTR': 'h6'}),
            (12, sp('_v_v_rel'), 'h7', {'ARG0': 'e2', 'ARG1': 'x4'})
        ])
        assert len(x.eps()) == 3
        assert x.eps()[0][1] == sp('_n_n_rel')
        assert x.eps()[1][1] == sp('_q_q_rel')
        assert x.eps()[2][1] == sp('_v_v_rel')
        # make sure order is preserved
        x = Xmrs()
        x.add_eps([
            (12, sp('_v_v_rel'), 'h7', {'ARG0':'e2', 'ARG1': 'x4'}),
            (11, sp('_q_q_rel'), 'h5', {'ARG0':'x4', 'RSTR': 'h6'}),
            (10, sp('_n_n_rel'), 'h3', {'ARG0':'x4'})
        ])
        assert x.eps()[0][1] == sp('_v_v_rel')
        assert x.eps()[1][1] == sp('_q_q_rel')
        assert x.eps()[2][1] == sp('_n_n_rel')

    def test_variables(self):
        sp = Pred.stringpred
        # variables can be passed in with properties
        x = Xmrs(vars={'x1':{'PERS':'3','NUM':'sg'}, 'e2':{'SF':'prop'}})
        assert len(x.variables()) == 2
        assert x.properties('x1')['PERS'] == '3'
        assert x.properties('e2')['SF'] == 'prop'
        # variables can also be inferred from structural things
        x = Xmrs(top='h0', index='e2', xarg='e5')
        assert set(x.variables()) == {'h0', 'e2', 'e5'}
        x = Xmrs(eps=[(10, sp('_n_n_rel'), 'h3', {'ARG0': 'x4'})])
        assert set(x.variables()) == {'x4', 'h3'}
        x = Xmrs(hcons=[('h0', 'qeq', 'h1')])
        assert set(x.variables()) == {'h0', 'h1'}
        x = Xmrs(icons=[('x4', 'focus', 'x6')])
        assert set(x.variables()) == {'x4', 'x6'}
        # variables can be passed in and inferred
        x = Xmrs(icons=[('x4', 'focus', 'x6')], vars={'x4': {'PERS': '3'}})
        assert set(x.variables()) == {'x4', 'x6'}
        assert x.properties('x4') == {'PERS': '3'}
        assert x.properties('x6') == {}
        # adding things later doesn't reset properties
        x = Xmrs(vars={'x4': {'PERS': '3'}})
        x.add_eps([(10, sp('_n_n_rel'), 'h3', {'ARG0': 'x4'})])
        assert set(x.variables()) == {'x4', 'h3'}
        assert x.properties('x4') == {'PERS': '3'}
        # and properties can't be added via properties()
        x.properties('x4')['NUM'] = 'sg'
        assert x.properties('x4') == {'PERS': '3'}
        # TODO: how do we add properties?
        # constants are not variables
        x = Xmrs(eps=[(10, sp('_v_v_rel'), 'h3',
                       {'ARG0': 'e2', 'CARG': '"dog"'})])
        assert set(x.variables()) == {'e2', 'h3'}
        # Constants don't need to be the CARG role, and don't need
        # quotes (but if there are quotes, even var-looking things are
        # constants). pyDelphin differs from the LKB in the first
        # respect, but also maybe in the second.
        x = Xmrs(eps=[(10, sp('_v_v_rel'), 'h3',
                       {'ARG0': 'e2', 'ARG1': '1', 'ARG2': '"x5"'})])
        assert set(x.variables()) == {'h3', 'e2'}

    def test___eq__(self):
        pass

    def test___contains__(self):
        pass

    def test_outgoing_args(self):
        pass

    def test_incoming_args(self):
        pass

    def test_is_connected(self):
        # empty Xmrs objects cannot be checked for connectedness
        with pytest.raises(XmrsError):
            Xmrs().is_connected()
        with pytest.raises(XmrsError):
            Xmrs(top='h0').is_connected()
        with pytest.raises(XmrsError):
            Xmrs(hcons=[('h0', 'qeq', 'h1')]).is_connected()
        # just a pred is fine (even without ARG0)
        x = Xmrs(eps=[(10, Pred.stringpred('_v_v_rel'), 'h1', {})])
        assert x.is_connected() == True
        x = Xmrs(eps=[(10, Pred.stringpred('_v_v_rel'), 'h1',
                       {'ARG0':'e2'})])
        assert x.is_connected() == True
        # disconnected top is fine
        x = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > ]')
        assert x.is_connected() == True
        # and a broken HCONS is ok, too?  (maybe revise later)
        x = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > '
                 '  HCONS: < h0 qeq h2 > ]')
        assert x.is_connected() == True
        # two disconnected EPs are definitely bad
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ]'
                 '          [ _n_n_rel LBL: h3 ARG0: x4 ] > ]')
        assert x.is_connected() == False
        # if they're linked, they're fine again
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ARG1: x4 ]'
                 '          [ _n_n_rel LBL: h3 ARG0: x4 ] > ]')
        assert x.is_connected() == True
        # they can also be linked by LBL
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ]'
                 '          [ _v_v_rel LBL: h1 ARG0: e4 ] > ]')
        # or by handle arguments
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ARG1: h3 ]'
                 '          [ _v_v_rel LBL: h3 ARG0: e4 ] > ]')
        assert x.is_connected() == True
        # or by qeqs
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ARG1: h3 ]'
                 '          [ _v_v_rel LBL: h5 ARG0: e4 ] > '
                 '  HCONS: < h3 qeq h5 > ]')
        assert x.is_connected() == True
        # simply being connected to something isn't enough
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ARG1: x4 ]'
                 '          [ _n_n_rel LBL: h3 ARG0: x4 ]'
                 '          [ _v_v_rel LBL: h5 ARG0: e6 ARG1: x8 ]'
                 '          [ _n_n_rel LBL: h7 ARG0: x8 ] > ]')
        assert x.is_connected() == False
        # some linkage needs to connect disparate subgraphs (even weird ones)
        x = read('[ TOP: h0 '
                 '  RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ARG1: x4 ]'
                 '          [ _n_n_rel LBL: h3 ARG0: x4 ]'
                 '          [ _v_v_rel LBL: h5 ARG0: e2 ARG1: x8 ]'
                 '          [ _n_n_rel LBL: h7 ARG0: x8 ] > ]')
        assert x.is_connected() == True


    def test_is_well_formed(self):
        pass

    def test_subgraph(self):
        pass
