# -*- coding: UTF-8 -*-

import pytest

from delphin.mrs.components import Pred, Node, Link, nodes, links
from delphin.mrs import Dmrs
from delphin.mrs.config import UNKNOWNSORT
#from delphin.mrs import simplemrs  # for convenience in later tests
from delphin.exceptions import XmrsError

sp = Pred.surface


# for convenience
def check_xmrs(x, top, index, xarg, eplen, hconslen, iconslen, varslen):
    assert x.top == top
    assert x.index == index
    assert x.xarg == xarg
    assert len(x.eps()) == eplen
    assert len(x.hcons()) == hconslen
    assert len(x.icons()) == iconslen
    assert len(x.variables()) == varslen


class TestDmrs():
    def test_empty(self):
        x = Dmrs()
        # Dmrs view
        assert len(nodes(x)) == 0
        assert len(links(x)) == 0
        # Xmrs members
        check_xmrs(x, None, None, None, 0, 0, 0, 0)

    def test_single_node(self):
        # basic, one Node, no TOP
        x = Dmrs(nodes=[Node(10, sp('"_rain_v_1_rel"'))])
        check_xmrs(x, None, None, None, 1, 0, 0, 2)
        # variables don't need to be created predictably, but it's nice
        # to get the expected values for simple cases
        assert x.label(10) == 'h1'
        assert x.ep(10).iv == 'u2'
        # now with cvarsort
        x = Dmrs(nodes=[Node(10, sp('"_rain_v_1_rel"'), {'cvarsort': 'e'})])
        check_xmrs(x, None, None, None, 1, 0, 0, 2)
        assert x.label(10) == 'h1'
        assert x.ep(10).iv == 'e2'
        # now with TOP
        x = Dmrs(
            nodes=[Node(10, sp('"_rain_v_1_rel"'), {'cvarsort': 'e'})],
            links=[Link(0, 10, None, 'H')]
        )
        check_xmrs(x, 'h0', None, None, 1, 1, 0, 3)
        assert x.label(10) == 'h1'
        assert x.ep(10).iv == 'e2'

    def test_to_dict(self):
        assert Dmrs().to_dict() == {'nodes': [], 'links': []}

        x = Dmrs(nodes=[Node(10, sp('"_rain_v_1_rel"'))])
        assert x.to_dict() == {
            'nodes': [{'nodeid': 10, 'predicate': '_rain_v_1',
                       'sortinfo': {'cvarsort': UNKNOWNSORT}}],
            'links': []
        }

        x = Dmrs(
            nodes=[Node(10, sp('"_rain_v_1_rel"'), {'cvarsort': 'e'})],
            links=[Link(0, 10, None, 'H')]
        )
        assert x.to_dict() == {
            'nodes': [{'nodeid': 10, 'predicate': '_rain_v_1',
                       'sortinfo': {'cvarsort': 'e'}}],
            'links': [{'from': 0, 'to': 10, 'rargname': None, 'post': 'H'}]
        }
        assert x.to_dict(properties=False) == {
            'nodes': [{'nodeid': 10, 'predicate': '_rain_v_1'}],
            'links': [{'from': 0, 'to': 10, 'rargname': None, 'post': 'H'}]
        }

    def test_from_dict(self):
        assert Dmrs.from_dict({}) == Dmrs()

        d1 = Dmrs.from_dict({
            'nodes': [{'nodeid': 10, 'predicate': '_rain_v_1'}],
            'links': [{'from': 0, 'to': 10, 'rargname': None, 'post': 'H'}],
        })
        d2 = Dmrs(nodes=[Node(10, sp('"_rain_v_1_rel"'))],
                  links=[Link(0, 10, None, 'H')])
        assert d1 == d2

    def test_to_triples(self):
        assert Dmrs().to_triples() == []

        x = Dmrs(nodes=[Node(10, sp('"_rain_v_1_rel"'))])
        assert x.to_triples() == [
            (10, 'predicate', '_rain_v_1'),
            (10, 'cvarsort', 'u')
        ]

        x = Dmrs(
            nodes=[Node(10, sp('"_rain_v_1_rel"'), {'cvarsort': 'e'})],
            links=[Link(0, 10, None, 'H')]
        )
        assert x.to_triples() == [
            (10, 'predicate', '_rain_v_1'),
            (10, 'cvarsort', 'e'),
            (0, 'top', 10)
        ]
        assert x.to_triples(properties=False) == [
            (10, 'predicate', '_rain_v_1'),
            (0, 'top', 10)
        ]

    def test_from_triples(self):
        assert Dmrs.from_triples([]) == Dmrs()

        d1 = Dmrs.from_triples([
            (10, 'predicate', '_rain_v_1'),
            (0, 'top', 10)
        ])
        # by default nodeids get remapped from 10000
        d2 = Dmrs(nodes=[Node(10000, sp('"_rain_v_1_rel"'))],
                  links=[Link(0, 10000, None, 'H')])
        assert d1 == d2
        d1 = Dmrs.from_triples([
            (10, 'predicate', '_rain_v_1'),

        ])
        assert d1 == d2

        d1 = Dmrs.from_triples([
            (10, 'predicate', '_rain_v_1'),
            (20, 'predicate', '_or_c'),
            (30, 'predicate', '_snow_v_1'),
            (0, 'top', 20),
            (20, 'L-INDEX-NEQ', 10),
            (20, 'L-HNDL-HEQ', 10),
            (20, 'R-INDEX-NEQ', 30),
            (20, 'R-HNDL-HEQ', 30)
        ])
        d2 = Dmrs(nodes=[Node(10000, sp('"_rain_v_1_rel"')),
                         Node(10001, sp('_or_c_rel')),
                         Node(10002, sp('"_snow_v_1_rel"'))],
                  links=[Link(0, 10001, None, 'H'),
                         Link(10001, 10000, 'L-INDEX', 'NEQ'),
                         Link(10001, 10000, 'L-HNDL', 'HEQ'),
                         Link(10001, 10002, 'R-INDEX', 'NEQ'),
                         Link(10001, 10002, 'R-HNDL', 'HEQ')])
        assert d1 == d2

