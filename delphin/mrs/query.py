"""
Functions for inspecting and interpreting the structure of an Xmrs.
"""

import warnings
from itertools import product

from delphin.mrs.components import nodes, links, var_id
from delphin.mrs.util import rargname_sortkey

# query methods
def select_nodeids(xmrs, iv=None, label=None, pred=None):
    """
    Return the list of all nodeids whose respective [EP] has the
    matching *iv* (intrinsic variable), *label*, or *pred* values. If
    none match, return an empty list.
    """
    def datamatch(nid):
        ep = xmrs.ep(nid)
        return ((iv is None or ep.iv == iv) and
                (pred is None or ep.pred == pred) and
                (label is None or ep.label == label))
    return list(filter(datamatch, xmrs.nodeids()))


def select_nodes(xmrs, nodeid=None, pred=None):
    """
    Return the list of all [Nodes] that have the matching *nodeid*
    and/or *pred* values. If none match, return an empty list.
    """
    nodematch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                           (pred is None or n.pred == pred))
    return list(filter(nodematch, nodes(xmrs)))


def select_eps(xmrs, nodeid=None, iv=None, label=None, pred=None):
    """
    Return the list of all [EPs] that have the matching *nodeid*,
    *iv*, *label*, and or *pred* values. If none match, return an
    empty list.
    """
    epmatch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                         (iv is None or n.iv == iv) and
                         (label is None or n.label == label) and
                         (pred is None or n.pred == pred))
    return list(filter(epmatch, xmrs.eps()))


def select_args(xmrs, nodeid=None, rargname=None, value=None):
    """
    Return a list of triples (nodeid, rargname, value) for all arguments
    matching *nodeid*, *rargname*, and/or *value* values. If none match,
    return an empty list.
    """
    argmatch = lambda a: ((nodeid is None or a[0] == nodeid) and
                          (rargname is None or
                           a[1].upper() == rargname.upper()) and
                          (value is None or a[2] == value))
    all_args = (
        (nid, role, val)
        for nid in xmrs.nodeids()
        for role, val in sorted(
            xmrs.args(nid).items(),
            key=lambda i: rargname_sortkey(i[0])
        )
    )
    return list(filter(argmatch, all_args))


def select_links(xmrs, start=None, end=None, rargname=None, post=None):
    """
    Return the list of all [Links] that have the matching *start*,
    *end*, *rargname*, and/or *post* values. If none match, return
    an empty list.
    """
    linkmatch = lambda l: (
        (start is None or l.start == start) and
        (end is None or l.end == end) and
        (rargname is None or l.rargname == rargname) and
        (post is None or l.post == post))
    return list(filter(linkmatch, links(xmrs)))


def select_hcons(xmrs, hi=None, relation=None, lo=None):
    """
    Return the list of all [HandleConstraints] that have the matching
    *hi*, *relation*, and/or *lo* values. If none match, return an
    empty list.
    """
    hcmatch = lambda hc: (
        (hi is None or hc.hi == hi) and
        (relation is None or hc.relation == relation) and
        (lo is None or hc.lo == lo))
    return list(filter(hcmatch, xmrs.hcons()))


def select_icons(xmrs, left=None, relation=None, right=None):
    """
    Return the list of all [IndividualConstraints] that have the
    matching *left*, *relation*, and/or *right* values. If none
    match, return an empty list.
    """
    icmatch = lambda ic: (
        (left is None or ic.left == left) and
        (relation is None or ic.relation == relation) and
        (right is None or ic.right == right))
    return list(filter(icmatch, xmrs.icons()))


def find_argument_target(xmrs, nodeid, rargname):
    """
    Return the target of an argument (rather than just the variable).

    Args:
        xmrs: The [Xmrs] object to use.
        nodeid: The nodeid of the argument.
        rargname: The role-argument name of the argument.
    Returns:
        The object that is the target of the argument. Possible values
        include:

        | Arg value          | e.g.  | Target                        |
        | ------------------ | ----- | ----------------------------- |
        | intrinsic variable | x4    | nodeid; of the EP with the IV |
        | hole variable      | h0    | nodeid; HCONS's labelset head |
        | label              | h1    | nodeid; label's labelset head |
        | unbound variable   | i3    | the variable itself           |
        | constant           | "IBM" | the constant itself           |

    Note:
        If the argument value is an intrinsic variable whose target is
        an EP that has a quantifier, the non-quantifier EP's nodeid
        will be returned. With this nodeid, one can then use
        find_quantifier() to get its quantifier's nodeid.
    """
    tgt = xmrs.args(nodeid)[rargname]
    if tgt in xmrs.variables():
        try:
            return xmrs.nodeid(tgt)
        except KeyError:
            pass

        try:
            tgt = xmrs.hcon(tgt).lo
            return next(iter(xmrs.labelset_heads(tgt)), None)
        except KeyError:
            pass

        try:
            return next(iter(xmrs.labelset_heads(tgt)))
        except (KeyError, StopIteration):
            pass
    return tgt


def find_subgraphs_by_preds(xmrs, preds, connected=None):
    """
    Yield subgraphs matching a list of preds. Because preds may match
    multiple EPs/nodes in the Xmrs, more than one subgraph is
    possible.

    Args:
        xmrs: The [Xmrs] object to use.
        preds: An iterable of [Preds] to include in subgraphs.
        connected: If True, all yielded subgraphs must be connected,
            as determined by Xmrs.is_connected().
    Yields:
        [Xmrs] objects for the found subgraphs.
    """
    preds = list(preds)
    count = len(preds)
    # find all lists of nodeids such that the lists have no repeated nids;
    # keep them as a list (fixme: why not just get sets?)
    nidsets = set(
        tuple(sorted(ns))
        for ns in filter(
            lambda ns: len(set(ns)) == count,
            product(*[select_nodeids(xmrs, pred=p) for p in preds])
        )
    )
    for nidset in nidsets:
        sg = xmrs.subgraph(nidset)
        if connected is None or sg.is_connected() == connected:
            yield sg


# def introduced_variables(xmrs):
#     return [var for var, vd in xmrs._vars.items()
#             if 'iv' in vd or 'LBL' in vd['refs'] or 'hcons' in vd]

def intrinsic_variable(xmrs, nid):
    return xmrs.ep(nid).intrinsic_variable

def intrinsic_variables(xmrs):
    ivs = set(
        ep.intrinsic_variable for ep in xmrs.eps()
        if not ep.is_quantifier() and ep.intrinsic_variable is not None
    )
    return sorted(ivs, key=var_id)

def bound_variables(xmrs):
    bvs = set(
        ep.intrinsic_variable for ep in xmrs.eps()
        if ep.is_quantifier() and ep.intrinsic_variable is not None
    )
    return sorted(bvs, key=var_id)

def in_labelset(xmrs, nodeids, label=None):
    """
    Test if all nodeids share a label.

    Args:
        nodeids: An iterable of nodeids.
        label: If given, all nodeids must share this label.
    Returns:
        True if all nodeids share a label, otherwise False.
    """
    nodeids = set(nodeids)
    if label is None:
        label = xmrs.ep(next(iter(nodeids))).label
    return nodeids.issubset(xmrs._vars[label]['refs']['LBL'])


#def audit(xmrs): inspect well-formedness and report individual errors

# deprecated

def find_quantifier(xmrs, nodeid):
    warnings.warn(
        'find_quantifier() is deprecated; '
        'try xmrs.nodeid(xmrs.ep(nodeid).iv, quantifier=True)',
        DeprecationWarning
    )
    ep = xmrs.ep(nodeid)
    if not ep.is_quantifier():
        return xmrs.nodeid(xmrs.ep(nodeid).iv, quantifier=True)
    return None

def get_outbound_args(xmrs, nodeid, allow_unbound=True):
    warnings.warn(
        'get_outbound_args() is deprecated; '
        'try xmrs.outgoing_args(nodeid)',
        DeprecationWarning
    )
    tgts = set(intrinsic_variables(xmrs))
    tgts.update(xmrs.labels())
    tgts.update(hc.hi for hc in xmrs.hcons())
    return [
        (nodeid, role, val)
        for role, val in sorted(
            xmrs.outgoing_args(nodeid).items(),
            key=lambda r_v: rargname_sortkey(r_v[0])
        )
        if allow_unbound or val in tgts
    ]

def nodeid(xmrs, iv, quantifier=False):
    warnings.warn(
        'nodeid() is deprecated; '
        'try xmrs.nodeid(iv, quantifier=quantifier)',
        DeprecationWarning
    )
    return xmrs.nodeid(iv, quantifier=quantifier)
