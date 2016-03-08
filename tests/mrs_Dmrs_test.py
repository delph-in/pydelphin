# -*- coding: UTF-8 -*-

import pytest

from delphin.mrs.components import Pred, Node, Link, nodes, links
from delphin.mrs import Dmrs
#from delphin.mrs import simplemrs  # for convenience in later tests
from delphin._exceptions import XmrsError


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
        sp = Pred.stringpred
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
