"""
Functions for inspecting and interpreting the structure of an Xmrs.
"""

from itertools import product

from delphin.mrs.components import nodes, links, var_id
from delphin.mrs.util import rargname_sortkey
from delphin.util import deprecated

# query methods
def select_nodeids(xmrs, iv=None, label=None, pred=None):
    """
    Return the list of matching nodeids in *xmrs*.

    Nodeids in *xmrs* match if their corresponding
    :class:`~delphin.mrs.components.ElementaryPredication` object
    matches its `intrinsic_variable` to *iv*, `label` to *label*,
    and `pred` to *pred*. The *iv*, *label*, and *pred* filters are
    ignored if they are `None`.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        iv (str, optional): intrinsic variable to match
        label (str, optional): label to match
        pred (str, :class:`~delphin.mrs.components.Pred`, optional):
            predicate to match
    Returns:
        list: matching nodeids
    """
    def datamatch(nid):
        ep = xmrs.ep(nid)
        return ((iv is None or ep.iv == iv) and
                (pred is None or ep.pred == pred) and
                (label is None or ep.label == label))
    return list(filter(datamatch, xmrs.nodeids()))


def select_nodes(xmrs, nodeid=None, pred=None):
    """
    Return the list of matching nodes in *xmrs*.

    DMRS :class:`nodes <delphin.mrs.components.node>` for *xmrs* match
    if their `nodeid` matches *nodeid* and `pred` matches *pred*. The
    *nodeid* and *pred* filters are ignored if they are `None`.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        nodeid (optional): DMRS nodeid to match
        pred (str, :class:`~delphin.mrs.components.Pred`, optional):
            predicate to match
    Returns:
        list: matching nodes
    """
    nodematch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                           (pred is None or n.pred == pred))
    return list(filter(nodematch, nodes(xmrs)))


def select_eps(xmrs, nodeid=None, iv=None, label=None, pred=None):
    """
    Return the list of matching elementary predications in *xmrs*.

    :class:`~delphin.mrs.components.ElementaryPredication` objects for
    *xmrs* match if their `nodeid` matches *nodeid*,
    `intrinsic_variable` matches *iv*, `label` matches *label*, and
    `pred` to *pred*. The *nodeid*, *iv*, *label*, and *pred* filters
    are ignored if they are `None`.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        nodeid (optional): nodeid to match
        iv (str, optional): intrinsic variable to match
        label (str, optional): label to match
        pred (str, :class:`~delphin.mrs.components.Pred`, optional):
            predicate to match
    Returns:
        list: matching elementary predications
    """
    epmatch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                         (iv is None or n.iv == iv) and
                         (label is None or n.label == label) and
                         (pred is None or n.pred == pred))
    return list(filter(epmatch, xmrs.eps()))


def select_args(xmrs, nodeid=None, rargname=None, value=None):
    """
    Return the list of matching (nodeid, role, value) triples in *xmrs*.

    Predication arguments in *xmrs* match if the `nodeid` of the
    :class:`~delphin.mrs.components.ElementaryPredication` they are
    arguments of match *nodeid*, their role matches *rargname*, and
    their value matches *value*. The *nodeid*, *rargname*, and *value*
    filters are ignored if they are `None`.

    Note:
        The *value* filter matches the variable, handle, or constant
        that is the overt value for the argument. If you want to find
        arguments that target a particular nodeid, look into
        :meth:`Xmrs.incoming_args() <delphin.mrs.xmrs.Xmrs.incoming_args>`.
        If you want to match a target value to its resolved object, see
        :func:`find_argument_target`.
    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        nodeid (optional): nodeid to match
        rargname (str, optional): role name to match
        value (str, optional): argument value to match
    Returns:
        list: matching arguments as (nodeid, role, value) triples
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
    Return the list of matching links for *xmrs*.

    :class:`~delphin.mrs.components.Link` objects for *xmrs* match if
    their `start` matches *start*, `end` matches *end*, `rargname`
    matches *rargname*, and `post` matches *post*. The *start*, *end*,
    *rargname*, and *post* filters are ignored if they are `None`.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        start (optional): link start nodeid to match
        end (optional): link end nodeid to match
        rargname (str, optional): role name to match
        post (str, optional): Link post-slash label to match
    Returns:
        list: matching links
    """
    linkmatch = lambda l: (
        (start is None or l.start == start) and
        (end is None or l.end == end) and
        (rargname is None or l.rargname == rargname) and
        (post is None or l.post == post))
    return list(filter(linkmatch, links(xmrs)))


def select_hcons(xmrs, hi=None, relation=None, lo=None):
    """
    Return the list of matching HCONS for *xmrs*.

    :class:`~delphin.mrs.components.HandleConstraint` objects for
    *xmrs* match if their `hi` matches *hi*, `relation` matches
    *relation*, and `lo` matches *lo*. The *hi*, *relation*, and *lo*
    filters are ignored if they are `None`.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        hi (str, optional): hi handle (hole) to match
        relation (str, optional): handle constraint relation to match
        lo (str, optional): lo handle (label) to match
    Returns:
        list: matching HCONS
    """
    hcmatch = lambda hc: (
        (hi is None or hc.hi == hi) and
        (relation is None or hc.relation == relation) and
        (lo is None or hc.lo == lo))
    return list(filter(hcmatch, xmrs.hcons()))


def select_icons(xmrs, left=None, relation=None, right=None):
    """
    Return the list of matching ICONS for *xmrs*.

    :class:`~delphin.mrs.components.IndividualConstraint` objects for
    *xmrs* match if their `left` matches *left*, `relation` matches
    *relation*, and `right` matches *right*. The *left*, *relation*,
    and *right* filters are ignored if they are `None`.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            query
        left (str, optional): left variable to match
        relation (str, optional): individual constraint relation to match
        right (str, optional): right variable to match
    Returns:
        list: matching ICONS
    """
    icmatch = lambda ic: (
        (left is None or ic.left == left) and
        (relation is None or ic.relation == relation) and
        (right is None or ic.right == right))
    return list(filter(icmatch, xmrs.icons()))


def find_argument_target(xmrs, nodeid, rargname):
    """
    Return the target of an argument (rather than just the variable).

    Note:
        If the argument value is an intrinsic variable whose target is
        an EP that has a quantifier, the non-quantifier EP's nodeid
        will be returned. With this nodeid, one can then use
        :meth:`Xmrs.nodeid() <delphin.mrs.xmrs.Xmrs.nodeid>` to get its
        quantifier's nodeid.
    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            use
        nodeid: nodeid of the argument.
        rargname: role name of the argument.
    Returns:
        The object that is the target of the argument. Possible values
        include:

        ==================  =====  =============================
        Argument value      e.g.   Target
        ------------------  -----  -----------------------------
        intrinsic variable  x4     nodeid; of the EP with the IV
        hole variable       h0     nodeid; HCONS's labelset head
        label               h1     nodeid; label's labelset head
        unbound variable    i3     the variable itself
        constant            "IBM"  the constant itself
        ==================  =====  =============================
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
    Yield subgraphs matching a list of predicates.

    Predicates may match multiple EPs/nodes in the *xmrs*, meaning that
    more than one subgraph is possible. Also, predicates in *preds*
    match in number, so if a predicate appears twice in *preds*, there
    will be two matching EPs/nodes in each subgraph.

    Args:
        xmrs (:class:`~delphin.mrs.xmrs.Xmrs`): semantic structure to
            use
        preds: iterable of predicates to include in subgraphs
        connected (bool, optional): if `True`, all yielded subgraphs
            must be connected, as determined by
            :meth:`Xmrs.is_connected() <delphin.mrs.xmrs.Xmrs.is_connected>`.
    Yields:
        A :class:`~delphin.mrs.xmrs.Xmrs` object for each subgraphs found.
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

def intrinsic_variables(xmrs):
    """Return the list of all intrinsic variables in *xmrs*"""
    ivs = set(
        ep.intrinsic_variable for ep in xmrs.eps()
        if not ep.is_quantifier() and ep.intrinsic_variable is not None
    )
    return sorted(ivs, key=var_id)

def bound_variables(xmrs):
    """Return the list of all bound variables in *xmrs*"""
    bvs = set(
        ep.intrinsic_variable for ep in xmrs.eps()
        if ep.is_quantifier() and ep.intrinsic_variable is not None
    )
    return sorted(bvs, key=var_id)

def in_labelset(xmrs, nodeids, label=None):
    """
    Test if all nodeids share a label.

    Args:
        nodeids: iterable of nodeids
        label (str, optional): the label that all nodeids must share
    Returns:
        bool: `True` if all nodeids share a label, otherwise `False`
    """
    nodeids = set(nodeids)
    if label is None:
        label = xmrs.ep(next(iter(nodeids))).label
    return nodeids.issubset(xmrs._vars[label]['refs']['LBL'])


# deprecated

@deprecated(final_version='1.0.0',
            alternative='xmrs.ep(nid).intrinsic_variable')
def intrinsic_variable(xmrs, nid):
    return xmrs.ep(nid).intrinsic_variable

@deprecated(final_version='1.0.0',
            alternative='xmrs.nodeid(xmrs.ep(nodeid).iv, quantifier=True)')
def find_quantifier(xmrs, nodeid):
    ep = xmrs.ep(nodeid)
    if not ep.is_quantifier():
        return xmrs.nodeid(xmrs.ep(nodeid).iv, quantifier=True)
    return None

@deprecated(final_version='1.0.0',
            alternative='xmrs.outgoing_args(nodeid)')
def get_outbound_args(xmrs, nodeid, allow_unbound=True):
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

@deprecated(final_version='1.0.0',
            alternative='xmrs.nodeid(iv, quantifier=quantifier)')
def nodeid(xmrs, iv, quantifier=False):
    return xmrs.nodeid(iv, quantifier=quantifier)
