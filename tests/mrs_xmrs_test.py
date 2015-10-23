# -*- coding: UTF-8 -*-

import pytest

from delphin.mrs.components import Pred, Node, Link
from delphin.mrs.xmrs import Xmrs, Dmrs
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
        # nodeid, pred, and label (the minimum)
        x.add_eps([(10000, Pred.stringpred('_v_v_rel'), 'h1')])
        # make sure it was entered correctly and is unchanged
        assert len(x.eps()) == 1
        assert x.eps()[0][0] == 10000
        ep = x.ep(10000)
        assert isinstance(ep[1], Pred) and ep[1].string == '_v_v_rel'
        assert ep[2] == 'h1'

        # nodeid, pred, label, and argdict
        x = Xmrs()
        x.add_eps([(10000, Pred.stringpred('_v_v_rel'), 'h1', {})])
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
        with pytest.raises(XmrsError):
            x.add_hcons([('h0')])  # only hi
            x.add_hcons([('h0', 'qeq')])  # only hi and relation
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
        with pytest.raises(XmrsError):
            x.add_icons([('x0')])  # only left
            x.add_icons([('x0', 'topic')])  # only left and relation
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

    def test_ep(self):
        sp = Pred.stringpred
        x = Xmrs()
        with pytest.raises(TypeError):
            x.ep()
        with pytest.raises(KeyError):
            x.ep(10)
        x.add_eps([(10, sp('_n_n_rel'), 'h3', {'ARG0': 'x4'})])
        assert x.ep(10)[1] == sp('_n_n_rel')

    def test_eps(self):
        sp = Pred.stringpred
        x = Xmrs()
        assert len(x.eps()) == 0
        x.add_eps([(10, sp('_n_n_rel'), 'h3', {'ARG0': 'x4'})])
        eps = x.eps()
        assert len(eps) == 1
        assert eps[0][0] == 10
        assert eps[0][1] == sp('_n_n_rel')
        assert eps[0][2] == 'h3'
        assert eps[0][3] == {'ARG0': 'x4'}
        x.add_eps([
            (11, sp('_q_q_rel'), 'h5', {'ARG0': 'x4', 'RSTR': 'h6'}),
            (12, sp('_v_v_rel'), 'h7', {'ARG0': 'e2', 'ARG1': 'x4'})
        ])
        eps = x.eps()
        assert len(eps) == 3
        assert eps[0][1] == sp('_n_n_rel')
        assert eps[1][1] == sp('_q_q_rel')
        assert eps[2][1] == sp('_v_v_rel')
        # make sure order is preserved
        x = Xmrs()
        x.add_eps([
            (12, sp('_v_v_rel'), 'h7', {'ARG0':'e2', 'ARG1': 'x4'}),
            (11, sp('_q_q_rel'), 'h5', {'ARG0':'x4', 'RSTR': 'h6'}),
            (10, sp('_n_n_rel'), 'h3', {'ARG0':'x4'})
        ])
        eps = x.eps()
        assert eps[0][1] == sp('_v_v_rel')
        assert eps[1][1] == sp('_q_q_rel')
        assert eps[2][1] == sp('_n_n_rel')
        # only get with given nodeids and in that order
        eps = x.eps(nodeids=[10, 11])
        assert eps[0][1] == sp('_n_n_rel')
        assert eps[1][1] == sp('_q_q_rel')
        # but asking for a non-existing one raises a KeyError
        with pytest.raises(KeyError):
            x.eps(nodeids=[10, 13])

    def test_hcon(self):
        x = Xmrs()
        with pytest.raises(TypeError):
            x.hcon()
        with pytest.raises(KeyError):
            x.hcon('h0')
        x.add_hcons([('h0', 'qeq', 'h1')])
        assert x.hcon('h0') == ('h0', 'qeq', 'h1')
        with pytest.raises(KeyError):
            x.hcon('h1')

    def test_hcons(self):
        x = Xmrs()
        assert len(x.hcons()) == 0
        x.add_hcons([('h0', 'qeq', 'h1')])
        hcs = x.hcons()
        assert len(hcs) == 1
        assert hcs[0] == ('h0', 'qeq', 'h1')
        x.add_hcons([('h3', 'qeq', 'h5')])
        hcs = sorted(x.hcons())  # hcons are not stored in sorted order
        assert len(hcs) == 2
        assert hcs[1] == ('h3', 'qeq', 'h5')

    def test_icons(self):
        x = Xmrs()
        with pytest.raises(KeyError):
            x.icons(left='x5')
        assert len(x.icons()) == 0
        x.add_icons([('e2', 'topic', 'e5')])
        ics = x.icons()
        assert len(ics) == 1
        assert ics[0] == ('e2', 'topic', 'e5')
        x.add_icons([('e2', 'focus', 'x4'), ('x7', 'info-str', 'x9')])
        ics = x.icons(left='e2')  # icons are not stored sorted
        assert len(ics) == 2
        assert set(ics) == {('e2', 'topic', 'e5'), ('e2', 'focus', 'x4')}
        with pytest.raises(KeyError):
            assert len(x.icons(left='e5')) == 0
            assert len(x.icons(left='x4')) == 0
            assert len(x.icons(left='x9')) == 0
        assert len(x.icons(left='x7')) == 1

    def test_variables_and_properties(self):
        sp = Pred.stringpred
        # variables can be passed in with properties
        x = Xmrs(vars={'x1':{'PERS':'3','NUM':'sg'}, 'e2':{'SF':'prop'}})
        assert len(x.variables()) == 2
        assert x.properties('x1')['PERS'] == '3'
        assert x.properties('e2')['SF'] == 'prop'
        # when there's no EP, you cannot retrieve properties via a nodeid
        with pytest.raises(KeyError): x.properties(10)
        # but when an EP with an ARG0 exists, you can
        x.add_eps([(10, sp('_n_n_rel'), 'h3', {'ARG0': 'x1'})])
        assert x.properties(10) == {'PERS': '3', 'NUM': 'sg'}
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

    def test_pred(self):
        x = Xmrs()
        # KeyError on bad nodeid
        with pytest.raises(KeyError): x.pred(10)
        # but otherwise preds can be retrieved by nodeid
        x.add_eps([(10, Pred.stringpred('_n_n_rel'), 'h3', {'ARG0': 'x4'})])
        assert x.pred(10).string == '_n_n_rel'

    def test_preds(self):
        sp = Pred.stringpred
        x = Xmrs(
            eps=[
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2', 'ARG1': 'x4'}),
                (11, sp('_n_n_rel'), 'h5', {'ARG0': 'x4'}),
                (12, sp('q_q_rel'), 'h7', {'ARG0': 'x4', 'RSTR': 'h6'})
            ],
            hcons=[('h6', 'qeq', 'h5')]
        )
        # works like xmrs.pred(), but with a list of nodeids
        ps = x.preds([10, 11])
        assert [p.string for p in ps] == ['_v_v_rel', '_n_n_rel']
        # order should be preserved
        ps = x.preds([12, 11])
        assert [p.string for p in ps] == ['q_q_rel', '_n_n_rel']
        # KeyError on bad nodeid
        with pytest.raises(KeyError): x.preds([10, 11, 13])
        # with no arguments, all preds are returned in original order
        ps = x.preds()
        assert [p.string for p in ps] == ['_v_v_rel', '_n_n_rel', 'q_q_rel']
        x = Xmrs(
            eps=[
                (12, sp('q_q_rel'), 'h7', {'ARG0': 'x4', 'RSTR': 'h6'}),
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2', 'ARG1': 'x4'}),
                (11, sp('_n_n_rel'), 'h5', {'ARG0': 'x4'})
            ],
            hcons=[('h6', 'qeq', 'h5')]
        )
        ps = x.preds()
        assert [p.string for p in ps] == ['q_q_rel', '_v_v_rel', '_n_n_rel']

    def test_label(self):
        # retrieve the label for a single ep, or KeyError if no such nodeid
        x = Xmrs(eps=[(10, Pred.stringpred('_v_v_rel'), 'h3', {'ARG0': 'e2'})])
        assert x.label(10) == 'h3'
        with pytest.raises(KeyError): x.label(11)

    def test_labels(self):
        sp = Pred.stringpred
        # same as Xmrs.labels() but with a list of nodeids
        x = Xmrs(
            eps=[
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2', 'ARG1': 'x4'}),
                (11, sp('_n_n_rel'), 'h5', {'ARG0': 'x4'}),
                (12, sp('q_q_rel'), 'h7', {'ARG0': 'x4', 'RSTR': 'h6'})
            ],
            hcons=[('h6', 'qeq', 'h5')]
        )
        assert x.labels([10, 12]) == ['h3', 'h7']
        with pytest.raises(KeyError): x.labels([12, 13])
        # no argument means all labels, in EP order
        assert x.labels() == ['h3', 'h5', 'h7']

    def test_args(self):
        # return the argument dict of a nodeid, or KeyError for missing nodeid
        x = Xmrs(
            eps=[(10, Pred.stringpred('_v_v_rel'), 'h3',
                  {'ARG0': 'e2', 'ARG1': 'x4'})]
        )
        assert x.args(10) == {'ARG0': 'e2', 'ARG1': 'x4'}
        with pytest.raises(KeyError): x.args(11)
        # retrieved dict does not edit original
        x.args(10)['ARG1'] = 'x6'
        assert x.args(10)['ARG1'] == 'x4'
        # return empty arg dict for EP without specified args:
        x = Xmrs(eps=[(10, Pred.stringpred('_v_v_rel'), 'h3')])
        assert x.args(10) == {}

    def test_outgoing_args(self):
        sp = Pred.stringpred
        # Outgoing args are those that, from some start node, go to
        # another in some way. These ways include:
        # regular variable args
        x = Xmrs(
            eps=[
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2'}),
                (11, sp('_a_a_rel'), 'h5', {'ARG0': 'e4', 'ARG1': 'e2'})
            ]
        )
        assert x.outgoing_args(10) == {}  # no outgoing args
        assert x.outgoing_args(11) == {'ARG1': 'e2'}
        # label equality args
        x = Xmrs(
            eps=[
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2', 'ARG1': 'h5'}),
                (11, sp('_v_v_rel'), 'h5', {'ARG0': 'e4'})
            ],
        )
        assert x.outgoing_args(10) == {'ARG1': 'h5'}
        assert x.outgoing_args(11) == {}  # no outgoing args
        # handle constraints
        x = Xmrs(
            eps=[
                (11, sp('_n_n_rel'), 'h5', {'ARG0': 'x4'}),
                (12, sp('q_q_rel'), 'h7', {'ARG0': 'x4', 'RSTR': 'h6'})
            ],
            hcons=[('h6', 'qeq', 'h5')]
        )
        assert x.outgoing_args(11) == {}  # no outgoing args
        assert x.outgoing_args(12) == {'RSTR': 'h6'}  # not shared ARG0
        # basic label equality is not "outgoing"
        x = Xmrs(
            eps=[
                (11, sp('_nearly_x_deg_rel'), 'h5', {'ARG0': 'e4'}),
                (12, sp('q_q_rel'), 'h5', {'ARG0': 'x6', 'RSTR': 'h7'})
            ],
        )
        assert x.outgoing_args(11) == {}
        assert x.outgoing_args(12) == {}  # RSTR would be if HCONS was there

    def test_incoming_args(self):
        # incoming_args() is like the reverse of outgoing_args(), but
        # now it's many-to-one instead of one-to-many
        sp = Pred.stringpred
        x = Xmrs(
            eps=[
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2'}),
                (11, sp('_a_a_rel'), 'h5', {'ARG0': 'e4', 'ARG1': 'e2'})
            ]
        )
        assert x.incoming_args(10) == {11: {'ARG1': 'e2'}}
        assert x.incoming_args(11) == {}  # no incoming args
        # label equality args
        x = Xmrs(
            eps=[
                (10, sp('_v_v_rel'), 'h3', {'ARG0': 'e2', 'ARG1': 'h5'}),
                (11, sp('_v_v_rel'), 'h5', {'ARG0': 'e4'})
            ],
        )
        assert x.incoming_args(10) == {}  # no incoming args
        assert x.incoming_args(11) == {10: {'ARG1': 'h5'}}
        # handle constraints
        x = Xmrs(
            eps=[
                (11, sp('_n_n_rel'), 'h5', {'ARG0': 'x4'}),
                (12, sp('q_q_rel'), 'h7', {'ARG0': 'x4', 'RSTR': 'h6'})
            ],
            hcons=[('h6', 'qeq', 'h5')]
        )
        assert x.incoming_args(11) == {12: {'RSTR': 'h6'}}
        assert x.incoming_args(12) == {}  # no incoming args
        # basic label equality is not "incoming"
        x = Xmrs(
            eps=[
                (11, sp('_nearly_x_deg_rel'), 'h5', {'ARG0': 'e4'}),
                (12, sp('q_q_rel'), 'h5', {'ARG0': 'x6', 'RSTR': 'h7'})
            ],
        )
        assert x.incoming_args(11) == {}
        assert x.incoming_args(12) == {}


    def test___eq__(self):
        x = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > ]')
        # just a string
        assert x != '[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > ]'
        # comparing the same Xmrs objects is fine
        y = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > ]')
        assert x == y
        # different var names
        y = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e5 ] > ]')
        assert x != y
        # different var locations
        y = read('[ TOP: h1 RELS: < [ _v_v_rel LBL: h0 ARG0: e2 ] > ]')
        assert x != y
        # different var associations
        y = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h0 ARG0: e2 ] > ]')
        assert x != y
        # hcons vs none
        y = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > '
                 '  HCONS: < h0 qeq h1 > ]')
        assert x != y

    def test___contains__(self):
        x = Xmrs()
        assert 'x1' not in x
        assert 10000 not in x
        assert 0 not in x
        assert None not in x
        x = read('[ TOP: h0 ]')
        assert 'h0' in x
        assert 10000 not in x
        assert 0 not in x
        x = read('[ TOP: h0 RELS: < [ _v_v_rel LBL: h1 ARG0: e2 ] > ]')
        assert all(_ in x for _ in ('h0', 'h1', 'e2', 10000)) == True
        assert 10001 not in x
        assert '10000' not in x
        assert '_v_v_rel' not in x
        assert Pred.stringpred('_v_v_rel') not in x

    def test_labelset(self): pass
    def test_labelset_heads(self): pass

    def test_is_connected(self):
        # empty Xmrs objects cannot be checked for connectedness
        with pytest.raises(XmrsError):
            Xmrs().is_connected()
            Xmrs(top='h0').is_connected()
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
        nodes = [Node(1,Pred.stringpred('verb'))]
        links = [Link(0,1,'','H')]
        graph = Dmrs(nodes,links)
        new_graph = graph.subgraph([1])
        assert len(new_graph._eps) == 1
