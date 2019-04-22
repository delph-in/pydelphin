
from collections import defaultdict
from itertools import permutations, groupby, chain
from functools import partial

import networkx as nx

from delphin import predicate
from delphin.sembase import role_priority, property_priority
from delphin.mrs import CONSTANT_ROLE, INTRINSIC_ROLE

# NOTES:
#  the somewhat naive implementations in _node_isomorphic and
#  _var_isomorphic have terrible runtimes for the pathological case,
#  and I didn't finish the Turbo_ISO implementation before I had to
#  move on, so I'm conceding defeat for the time being and using
#  networkx just for isomorphism (so I build a nx DiGraph here, then
#  throw it away when i'm done).

def isomorphic(q, g, check_varprops=True):
    """
    Return `True` if Xmrs objects *q* and *g* are isomorphic.

    Isomorphicity compares the predicates of an Xmrs, the variable
    properties of their predications (if `check_varprops=True`),
    constant arguments, and the argument structure between
    predications. Node IDs and Lnk values are ignored.

    Args:
        q: the left Xmrs to compare
        g: the right Xmrs to compare
        check_varprops: if `True`, make sure variable properties are
            equal for mapped predications
    """

    qdg = _make_digraph(q, check_varprops)
    gdg = _make_digraph(g, check_varprops)
    def nem(qd, gd):  # node-edge-match
        return qd.get('sig') == gd.get('sig')
    return nx.is_isomorphic(qdg, gdg, node_match=nem, edge_match=nem)

def _make_digraph(x, check_varprops):
    dg = nx.DiGraph()
    # scope labels (may be targets of arguments or hcons)
    for label, eps in x.scopes().items():
        dg.add_edges_from((label, ep.iv, {'sig':'eq-scope'}) for ep in eps)
    # predicate-argument structure
    for ep in x.rels:
        iv, pred, args = ep.iv, ep.predicate, ep.args
        if ep.is_quantifier():
            iv += '(bound)'  # make sure node id is unique
        s = predicate.normalize(pred)
        if CONSTANT_ROLE in args:
            s += '({})'.format(args[CONSTANT_ROLE])
        if check_varprops and not ep.is_quantifier():
            props = x.variables[iv]
            s += '{{{}}}'.format('|'.join(
                '{}={}'.format(prop.upper(), props[prop].lower())
                for prop in sorted(props, key=property_priority)))
        dg.add_node(iv, sig=s)
        dg.add_edges_from((iv, args[role], {'sig': role})
                          for role in sorted(args, key=role_priority)
                          if role != CONSTANT_ROLE)
    # hcons
    dg.add_edges_from((hc.hi, hc.lo, {'sig':hc.relation})
                      for hc in x.hcons)
    # icons
    dg.add_edges_from((ic.left, ic.right, {'sig':ic.relation})
                      for ic in x.icons)
    return dg


def compare_bags(testbag, goldbag, count_only=True):
    """
    Compare two bags of Xmrs objects, returning a triple of
    (unique in test, shared, unique in gold).

    Args:
        testbag: An iterable of Xmrs objects to test.
        goldbag: An iterable of Xmrs objects to compare against.
        count_only: If True, the returned triple will only have the
            counts of each; if False, a list of Xmrs objects will be
            returned for each (using the ones from testbag for the
            shared set)
    Returns:
        A triple of (unique in test, shared, unique in gold), where
        each of the three items is an integer count if the count_only
        parameter is True, or a list of Xmrs objects otherwise.
    """
    gold_remaining = list(goldbag)
    test_unique = []
    shared = []
    for test in testbag:
        gold_match = None
        for gold in gold_remaining:
            if isomorphic(test, gold):
                gold_match = gold
                break
        if gold_match is not None:
            gold_remaining.remove(gold_match)
            shared.append(test)
        else:
            test_unique.append(test)
    if count_only:
        return (len(test_unique), len(shared), len(gold_remaining))
    else:
        return (test_unique, shared, gold_remaining)
