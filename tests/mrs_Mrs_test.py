# -*- coding: UTF-8 -*-

import pytest

from delphin.mrs.components import (
    Pred,
    ElementaryPredication as EP,
    elementarypredications as eps,
    HandleConstraint as Hcons,
    hcons,
    IndividualConstraint as Icons,
    icons,
)
from delphin.mrs.config import (FIRST_NODEID, UNKNOWNSORT)
from delphin.mrs import Mrs
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


class TestMrs():
    def test_empty(self):
        x = Mrs()
        # Mrs view
        assert len(eps(x)) == 0
        assert len(hcons(x)) == 0
        assert len(icons(x)) == 0
        # Xmrs members
        check_xmrs(x, None, None, None, 0, 0, 0, 0)

    def test_single_ep(self):
        # basic, one EP, no TOP
        x = Mrs(rels=[EP(10, sp('"_rain_v_1_rel"'), 'h1')])
        check_xmrs(x, None, None, None, 1, 0, 0, 1)
        # variables don't need to be created predictably, but it's nice
        # to get the expected values for simple cases
        assert x.label(10) == 'h1'
        assert x.ep(10).iv == None
        # now with ARG0
        x = Mrs(rels=[EP(10, sp('"_rain_v_1_rel"'), 'h1', {'ARG0': 'e2'})])
        check_xmrs(x, None, None, None, 1, 0, 0, 2)
        assert x.label(10) == 'h1'
        assert x.ep(10).iv == 'e2'
        # now with TOP
        x = Mrs(
            top='h0',
            rels=[EP(10, sp('"_rain_v_1_rel"'), 'h1', {'ARG0': 'e2'})],
            hcons=[('h0', 'qeq', 'h1')]
        )
        check_xmrs(x, 'h0', None, None, 1, 1, 0, 3)
        assert x.label(10) == 'h1'
        assert x.ep(10).iv == 'e2'

    def test_to_dict(self):
        assert Mrs().to_dict() == {
            'relations': [], 'constraints': [], 'variables': {}
        }

        x = Mrs(rels=[EP(10, sp('"_rain_v_1_rel"'), 'h1', {'ARG0': 'e2'})])
        assert x.to_dict() == {
            'relations': [
                {'label': 'h1', 'predicate': '_rain_v_1',
                 'arguments': {'ARG0': 'e2'}}
            ],
            'constraints': [],
            'variables': {'h1': {'type': 'h'}, 'e2': {'type': 'e'}}
        }

        x = Mrs(
            top='h0',
            rels=[EP(10, sp('"_rain_v_1_rel"'), 'h1', {'ARG0': 'e2'})],
            hcons=[('h0', 'qeq', 'h1')],
            vars={'e2': {'SF': 'prop', 'TENSE': 'pres'}}
        )
        assert x.to_dict() == {
            'top': 'h0',
            'relations': [
                {'label': 'h1', 'predicate': '_rain_v_1',
                 'arguments': {'ARG0': 'e2'}}
            ],
            'constraints': [{'relation': 'qeq', 'high': 'h0', 'low': 'h1'}],
            'variables': {
                'h0': {'type': 'h'}, 'h1': {'type': 'h'},
                'e2': {'type': 'e',
                       'properties': {'SF': 'prop', 'TENSE': 'pres'}}
            }
        }
        assert x.to_dict(properties=False) == {
            'top': 'h0',
            'relations': [
                {'label': 'h1', 'predicate': '_rain_v_1',
                 'arguments': {'ARG0': 'e2'}}
            ],
            'constraints': [{'relation': 'qeq', 'high': 'h0', 'low': 'h1'}],
            'variables': {
                'h0': {'type': 'h'}, 'h1': {'type': 'h'},
                'e2': {'type': 'e'}
            }
        }


    def test_from_dict(self):
        assert Mrs.from_dict({}) == Mrs()

        m1 = Mrs.from_dict({
            'relations': [
                {'label': 'h1', 'predicate': '_rain_v_1',
                 'arguments': {'ARG0': 'e2'}}
            ],
            'constraints': [],
            'variables': {
                'h1': {'type': 'h'},
                'e2': {'type': 'e',
                       'properties': {'SF': 'prop', 'TENSE': 'pres'}}
            }
        })
        m2 = Mrs(
            rels=[
                EP(FIRST_NODEID, sp('"_rain_v_1_rel"'), 'h1', {'ARG0': 'e2'})
            ],
            vars={'e2': {'SF': 'prop', 'TENSE': 'pres'}}
        )
        assert m1 == m2
