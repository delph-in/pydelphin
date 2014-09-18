from itertools import product

# query methods
def select_nodeids(xmrs, iv=None, label=None, pred=None):
    """
    Return the list of all nodeids whose respective |EP| has the
    matching *iv* (intrinsic variable), *label*, or *pred* values. If
    none match, return an empty list.
    """
    g = xmrs._graph
    nids = []
    datamatch = lambda d: ((iv is None or d['ep'].iv == iv) and
                           (pred is None or d['ep'].pred == pred) and
                           (label is None or d['label'] == label))
    for nid in g.nodeids:
        data = g.node[nid]
        if datamatch(data):
            nids.append(nid)
    return nids


def select_nodes(xmrs, nodeid=None, pred=None):
    """
    Return the list of all |Nodes| that have the matching *nodeid*
    and/or *pred* values. If none match, return an empty list.
    """
    nodematch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                           (pred is None or n.pred == pred))
    return list(filter(nodematch, xmrs.nodes))


def select_eps(xmrs, anchor=None, iv=None, label=None, pred=None):
    """
    Return the list of all |EPs| that have the matching *anchor*,
    *iv*, *label*, and or *pred* values. If none match, return an
    empty list.
    """
    epmatch = lambda n: ((anchor is None or n.anchor == anchor) and
                         (iv is None or n.iv == iv) and
                         (label is None or n.label == label) and
                         (pred is None or n.pred == pred))
    return list(filter(epmatch, xmrs.eps))


def select_args(xmrs, anchor=None, rargname=None, value=None):
    """
    Return the list of all |Arguments| that have the matching
    *anchor*, *rargname*, and/or *value* values. If none match,
    return an empty list.
    """
    argmatch = lambda a: ((anchor is None or a.anchor == anchor) and
                          (rargname is None or
                           a.argname.upper() == rargname.upper()) and
                          (value is None or a.value == value))
    return list(filter(argmatch, xmrs.args))


def select_links(xmrs, source=None, target=None, rargname=None, post=None):
    """
    Return the list of all |Links| that have the matching *source*,
    *target*, *rargname*, and/or *post* values. If none match, return
    an empty list.
    """
    linkmatch = lambda l: (
        (source is None or l.source == source) and
        (target is None or l.target == target) and
        (rargname is None or l.argname == rargname) and
        (post is None or l.post == post))
    return list(filter(linkmatch, xmrs.links))


def select_hcons(xmrs, hi=None, relation=None, lo=None):
    """
    Return the list of all |HandleConstraints| that have the matching
    *hi*, *relation*, and/or *lo* values. If none match, return an
    empty list.
    """
    hcmatch = lambda hc: (
        (hi is None or hc.hi == hi) and
        (relation is None or hc.relation == relation) and
        (lo is None or hc.lo == lo))
    return list(filter(hcmatch, xmrs.hcons))


def select_icons(xmrs, target=None, relation=None, clause=None):
    """
    Return the list of all |IndividualConstraints| that have the
    matching *target*, *relation*, and/or *clause* values. If none
    match, return an empty list.
    """
    icmatch = lambda ic: (
        (target is None or ic.target == target) and
        (relation is None or ic.relation == relation) and
        (clause is None or ic.clause == clause))
    return list(filter(icmatch, xmrs.icons))


def find_argument_target(xmrs, nodeid, rargname):
    """
    Return the target of an argument (rather than just the variable).

    Args:
        xmrs: The |Xmrs| object to use.
        nodeid: The nodeid (or anchor) of the argument.
        rargname: The role-argument name of the argument.
    Returns:
        The object that is the target of the argument. Possible values
        include:

        ================== =====  =================================
             Arg value     e.g.               Target
        ================== =====  =================================
        intrinsic variable x4     nodeid; of the EP with the IV
        hole variable      h0     nodeid; the HCONS's labelset head
        label              h1     nodeid; the label's labelset head
        unbound variable   i3     the variable itself
        constant           "IBM"  the constant itself
        ================== =====  =================================

    Note:
        If the argument value is an intrinsic variable whose target is
        an EP that has a quantifier, the non-quantifier EP's nodeid
        will be returned. With this nodeid, one can then use
        :py:meth:`find_quantifier` to get its quantifier's nodeid.
    """
    g = xmrs._graph
    tgt = None
    try:
        tgt_val = xmrs.get_arg(nodeid, rargname).value
        tgt_attr = g.node[tgt_val]

        # intrinsic variable
        if 'iv' in tgt_attr:
            tgt = tgt_attr['iv']

        # hcons; tgt_val is a hole
        if 'hcons' in tgt_attr:
            tgt_val = tgt_attr['hcons'].lo
        # label or hcons lo variable (see previous if block)
        if tgt_val in g.labels:
            tgt = xmrs.labelset_head(tgt_val)

        # otherwise likely a constant or unbound variable
        tgt = tgt_val

    # nodeid or rargname were missing, or tgt_val wasn't a node
    except (AttributeError, KeyError):
        pass
        #logging.warning('Cannot find argument target; argument is '
        #                'invalid: {}:{}'.format(nodeid, rargname))
    return tgt


def find_quantifier(xmrs, nodeid):
    """
    Return the nodeid of the quantifier of the EP given by `nodeid`.

    Args:
        xmrs: The |Xmrs| object to use.
        nodeid: The nodeid of the quantified EP/node.
    Returns:
        The nodeid of the quantifier for `nodeid`. If `nodeid` is not
        in the Xmrs, it itself is a quantifier, or if it does not have
        a quantifier, None is returned.
    """
    ep = xmrs.get_ep(nodeid)
    if not ep or ep.is_quantifier() or 'bv' not in xmrs._graph.node[ep.iv]:
        return None
    return xmrs._graph.node[ep.iv]['bv']


def get_outbound_args(xmrs, nodeid, allow_unbound=True):
    """
    Yield the |Arguments| of `nodeid` that point to other EPs/nodes.

    Args:
        xmrs: The |Xmrs| object to use.
        nodeid: The nodeid of the EP/node whose arguments to yield.
        allow_unbound: If True, also yield arguments that point to
            unbound (e.g. dropped) EPs/nodes or constants.
    Yields:
        |Arguments| whose targets are not the given `nodeid`.
    """
    g = xmrs._graph
    ep = xmrs.get_ep(nodeid)
    for arg in ep.args:
        nid = arg.nodeid
        tgt = arg.value
        data = g.node.get(tgt, {})
        # ignore intrinsic arguments
        if data.get('iv') == nid or data.get('bv') == nid:
            continue
        is_outbound = 'iv' in data or 'hcons' in data or tgt in g.labels
        if (allow_unbound or is_outbound):
            yield arg


def find_subgraphs_by_preds(xmrs, preds, connected=None):
    """
    Yield subgraphs matching a list of preds. Because preds may match
    multiple EPs/nodes in the Xmrs, more than one subgraph is
    possible.

    Args:
        xmrs: The |Xmrs| object to use.
        preds: An iterable of |Preds| to include in subgraphs.
        connected: If True, all yielded subgraphs must be connected,
            as determined by :py:meth:`Xmrs.is_connected`.
    Yields:
        |Xmrs| objects for the found subgraphs.
    """
    preds = list(preds)
    # find all lists of nodeids such that the lists have no repeated nids;
    # keep them as a list (fixme: why not just get sets?)
    nidsets = list(
        filter(lambda ps: len(set(ps)) == len(ps),
               map(lambda p: select_nodeids(xmrs, pred=p), preds))
    )
    for sg in map(xmrs.subgraph, product(*nidsets)):
        if connected is not None and sg.is_connected() != connected:
            continue
        yield sg
