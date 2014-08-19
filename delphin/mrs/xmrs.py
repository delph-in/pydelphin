import logging
from operator import or_
from copy import copy, deepcopy
from collections import (OrderedDict, defaultdict)
from itertools import chain, product
# consider using this:
# from functools import lru_cache
import networkx as nx
from delphin._exceptions import XmrsStructureError
from .components import (
    Hook, MrsVariable, ElementaryPredication, Node, Argument, Link,
    HandleConstraint, Lnk, LnkMixin
)
from .config import (
    HANDLESORT, IVARG_ROLE, CONSTARG_ROLE, LTOP_NODEID, FIRST_NODEID,
    RSTR_ROLE, EQ_POST, NEQ_POST, HEQ_POST, H_POST, NIL_POST
)
from .util import AccumulationDict as AccDict, XmrsDiGraph, first, second


def Mrs(hook=None, rels=None, hcons=None, icons=None,
        lnk=None, surface=None, identifier=None):
    """
    Construct an |Xmrs| using MRS components.

    Formally, Minimal Recursion Semantics (MRS) have a top handle, a
    bag of |ElementaryPredications|, and a bag of |HandleConstraints|.
    All |Arguments|, including intrinsic arguments and constant
    arguments, are expected to be contained by the |EPs|.

    Args:
        hook: A |Hook| object to contain LTOP, INDEX, etc.
        rels: An iterable of |ElementaryPredications|
        hcons: An iterable of |HandleConstraints|
        icons: An iterable of IndividualConstraints (planned feature)
        lnk: The |Lnk| object associating the MRS to the surface form
        surface: The surface string
        identifier: A discourse-utterance id
    Returns:
        An |Xmrs| object

    Example:

    >>> ltop = MrsVariable(vid=0, sort='h')
    >>> rain_label = MrsVariable(vid=1, sort='h')
    >>> index = MrsVariable(vid=2, sort='e')
    >>> m = Mrs(
    >>>     hook=Hook(ltop=ltop, index=index),
    >>>     rels=[ElementaryPredication(
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         label=rain_label,
    >>>         args=[Argument.mrs_argument('ARG0', index)]
    >>>         )
    >>>     ],
    >>>     hcons=[HandleConstraint(ltop, 'qeq', rain_label)]
    >>> )
    """
    if hook is None:
        hook = Hook()
    eps = list(rels or [])
    hcons = list(hcons or [])
    icons = list(icons or [])
    # first give eps a nodeid (this is propagated to args)
    next_nodeid = FIRST_NODEID
    for ep in eps:
        if ep.nodeid is not None and ep.nodeid >= next_nodeid:
            next_nodeid = ep.nodeid + 1
    for i, ep in enumerate(eps):
        if ep.nodeid is None:
            ep.nodeid = next_nodeid + i
    graph = build_graph(hook, eps, hcons, icons)
    return Xmrs(graph, hook, lnk, surface, identifier)


def Rmrs(hook=None, eps=None, args=None, hcons=None, icons=None,
         lnk=None, surface=None, identifier=None):
    """
    Construct an |Xmrs| from RMRS components.

    Robust Minimal Recursion Semantics (RMRS) are like MRS, but all
    |EPs| have an anchor (or nodeid), and |Arguments| are not contained
    by the source |EPs|, but instead reference the anchor of their |EP|.

    Args:
        hook: A |Hook| object
        eps: An iterable of |EP| objects
        args: An iterable of |Argument| objects
        hcons: An iterable of |HandleConstraint| objects
        icons: An iterable of |IndividualConstraint| objects
        lnk: A |Lnk| object
        surface: The surface string
        identifier: A discourse-utterance id
    Returns:
        An |Xmrs| object

    Example:

    >>> ltop = MrsVariable(vid=0, sort='h')
    >>> rain_label = MrsVariable(vid=1, sort='h')
    >>> rain_anchor = MrsVariable(vid=10000, sort='h')
    >>> index = MrsVariable(vid=2, sort='e')
    >>> m = Rmrs(
    >>>     hook=Hook(ltop=ltop, index=index),
    >>>     eps=[ElementaryPredication(
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         label=rain_label,
    >>>         anchor=rain_anchor
    >>>         )
    >>>     ],
    >>>     args=[Argument.rmrs_argument(rain_anchor, 'ARG0', index)],
    >>>     hcons=[HandleConstraint(ltop, 'qeq', rain_label)]
    >>> )
    """
    if hook is None:
        hook = Hook()
    eps = list(eps or [])
    args = list(args or [])
    for arg in args:
        if arg.nodeid is None:
            raise XmrsStructureError("RMRS args must have an anchor/nodeid.")
    # make the EPs more MRS-like (with arguments)
    for ep in eps:
        if ep.nodeid is None:
            raise XmrsStructureError("RMRS EPs must have an anchor/nodeid.")
        argdict = OrderedDict((a.argname, a) for a in args
                              if a.nodeid == ep.nodeid)
        ep.argdict = argdict
    hcons = list(hcons or [])
    icons = list(icons or [])
    graph = build_graph(hook, eps, hcons, icons)
    return Xmrs(graph, hook, lnk, surface, identifier)

def Dmrs(nodes=None, links=None,
         lnk=None, surface=None, identifier=None,
         **kwargs):
    """
    Construct an |Xmrs| using DMRS components.

    Dependency Minimal Recursion Semantics (DMRS) have a list of |Node|
    objects and a list of |Link| objects. There are no variables or
    handles, so these will need to be created in order to make an |Xmrs|
    object. A |Link| from the nodeid 0 (which does not have its own
    |Node|)

    Args:
        nodes: An iterable of |Node| objects
        links: An iterable of |Link| objects
        lnk: The |Lnk| object associating the MRS to the surface form
        surface: The surface string
        identifier: A discourse-utterance id
    Returns:
        An |Xmrs| object

    Example:

    >>> rain = Node(10000, Pred.stringpred('_rain_v_1_rel'),
    >>>             sortinfo={'cvarsort': 'e'})
    >>> ltop_link = Link(0, 10000, post='H')
    >>> d = Dmrs([rain], [ltop_link])
    """
    from .components import (VarGenerator, qeq)
    vgen = VarGenerator(starting_vid=0)
    labels = _make_labels(nodes, links, vgen)
    ivs = _make_ivs(nodes, vgen)
    hook = Hook(ltop=labels[LTOP_NODEID])  # no index for now
    # initialize args with ARG0 for intrinsic variables
    args = {nid: [Argument(nid, IVARG_ROLE, iv)] for nid, iv in ivs.items()}
    hcons = []
    for l in links:
        if l.start not in args:
            args[l.start] = []
        # FIXME: I don't have a clear answer about how LTOP links are
        # constructed, so I will assume that H_POST or NIL_POST
        # assumes a QEQ. Label equality would have been captured by
        # _make_labels() earlier.
        if l.start == LTOP_NODEID:
            if l.post == H_POST or l.post == NIL_POST:
                hcons += [qeq(labels[LTOP_NODEID], labels[l.end])]
        else:
            if l.argname is None:
                continue  # don't make an argument for bare EQ links
            if l.post == H_POST:
                hole = vgen.new(HANDLESORT)
                hcons += [qeq(hole, labels[l.end])]
                args[l.start].append(Argument(l.start, l.argname, hole))
                # if the arg is RSTR, it's a quantifier, so we can
                # find its intrinsic variable now
                if l.argname.upper() == RSTR_ROLE:
                    ivs[l.start] = ivs[l.end]
                    args[l.start].append(
                        Argument(l.start, IVARG_ROLE, ivs[l.start])
                    )
            elif l.post == HEQ_POST:
                args[l.start].append(
                    Argument(l.start, l.argname, labels[l.end])
                )
            else:  # NEQ_POST or EQ_POST
                args[l.start].append(
                    Argument(l.start, l.argname, ivs[l.end])
                )
    eps = []
    for node in nodes:
        nid = node.nodeid
        if node.carg is not None:
            args[nid].append(Argument(nid, CONSTARG_ROLE, node.carg))
        ep = ElementaryPredication.from_node(
            labels[nid], node, (args.get(nid) or None)
        )
        eps.append(ep)

    icons = None  # future feature
    return Mrs(hook=hook, rels=eps,
               hcons=hcons, icons=icons,
               lnk=lnk, surface=surface, identifier=identifier)


def _make_labels(nodes, links, vgen):
    labels = {}
    labels[LTOP_NODEID] = vgen.new(HANDLESORT)  # reserve h0 for ltop
    for l in links:
        if l.post == EQ_POST:
            lbl = (labels.get(l.start) or
                   labels.get(l.end) or
                   vgen.new(HANDLESORT))
            labels[l.start] = labels[l.end] = lbl
    # create any remaining uninstantiated labels
    for n in nodes:
        if n.nodeid not in labels:
            labels[n.nodeid] = vgen.new(HANDLESORT)
    return labels


def _make_ivs(nodes, vgen):
    ivs = {}
    for node in nodes:
        # quantifiers share their IV with the quantifiee. It will be
        # selected later during argument construction
        if not node.is_quantifier():
            ivs[node.nodeid] = vgen.new(node.cvarsort,
                                        node.properties or None)
    return ivs


def build_graph(hook, eps, hcons, icons):
    iv_to_nid = {ep.iv: ep.nodeid for ep in eps if not ep.is_quantifier()}
    # bv_to_nid = {ep.iv: ep.nodeid for ep in eps if ep.is_quantifier()}
    # lbl_to_nids = AccDict(or_, ((ep.label, {ep.nodeid}) for ep in eps))
    var_to_hcons = {hc.hi: hc for hc in hcons}
    g = XmrsDiGraph()
    for ep in eps:
        nid = ep.nodeid
        lbl = ep.label
        iv = ep.iv
        g.nodeids.append(nid)
        g.labels.add(lbl)
        g.add_node(nid, {'ep': ep, 'label': lbl})
        g.add_node(lbl)
        g.add_edge(lbl, nid)
        g.add_node(iv)
        if iv in iv_to_nid:
            g.add_edge(iv, nid, {'iv': True})  # intrinsic arg
        else:
            g.add_edge(iv, nid, {'bv': True})  # quantifier
    if hook.ltop is not None:
        g.add_node(LTOP_NODEID, label=hook.ltop)
        if hook.ltop in var_to_hcons:
            hc = var_to_hcons[hook.ltop]
            g.add_edge(LTOP_NODEID, hc.lo, {'hcons': hc})
        else:
            g.add_edge(LTOP_NODEID, hook.ltop)
    for arg in chain.from_iterable(ep.args for ep in eps):
        nid = arg.nodeid
        attrs = {'rargname': arg.argname, 'arg': arg}
        tgt = arg.value
        if arg.type == Argument.CONSTANT_ARG:
            continue
            # g.node[ep.nodeid][arg.argname] = str(val)
        elif tgt in iv_to_nid:
            # ARG0s (including quantifiers) don't get an arg edge
            if tgt == g.node[nid]['ep'].iv:
                continue
            tgt = iv_to_nid[tgt]
        elif tgt in var_to_hcons:
            hc = var_to_hcons[tgt]
            tgt = hc.lo
            attrs['hcons'] = hc
        g.add_edge(nid, tgt, attrs)
    return g


class Xmrs(LnkMixin):
    """
    Xmrs is a common class for Mrs, Rmrs, and Dmrs objects.
    """

    def __init__(self, graph=None, hook=None,
                 lnk=None, surface=None, identifier=None):
        """
        Xmrs can be instantiated directly, but it is meant to be created
        by the constructor methods :py:meth:`Mrs`, :py:meth:`Rmrs`, or
        :py:meth:`Dmrs`.

        Args:
            graph: a graph of the \*MRS structure
            hook: a |Hook| object to contain the ltop, xarg, and index
            lnk: the |Lnk| object associating the Xmrs to the surface form
            surface: the surface string
            identifier: a discourse-utterance id
        """
        self._graph = graph

        # Some members relate to the whole MRS
        #: The |Hook| object contains the LTOP, INDEX, and XARG
        self.hook = hook or Hook()
        #: A |Lnk| object to associate the Xmrs to the surface form
        self.lnk = lnk  # Lnk object (MRS-level lnk spans the whole input)
        #: The surface string
        self.surface = surface   # The surface string
        #: A discourse-utterance id
        self.identifier = identifier  # Associates an utterance with the RMRS

        # set the proper argument types (at least distinguish label
        # equality from HCONS)
        # for ep in eps:
        #     for arg in ep.args:
        #         arg.type = arg.infer_argument_type(xmrs=self)

    def __repr__(self):
        if self.surface is not None:
            stringform = '"{}"'.format(self.surface)
        else:
            stringform = ' '.join(ep.pred.lemma for ep in self.eps)
        return 'Xmrs({})'.format(stringform)

    # Interface layer to the internal representations (and part of the
    # public API)

    @property
    def nodeids(self):
        """
        The list of `nodeids`.
        """
        # does not return LTOP nodeid
        return list(self._graph.nodeids)

    @property
    def anchors(self):
        """
        The list of `anchors`.
        """
        # does not return LTOP anchor
        return list(ep.anchor for ep in self._nid_to_ep.values())

    @property
    def variables(self):
        """
        The list of all |MrsVariable| objects specified in the Xmrs.
        """
        return self.introduced_variables.union(
            [self.hook.ltop, self.hook.index] +
            [arg.value for ep in self.eps for arg in ep.args
             if isinstance(arg.value, MrsVariable)] +
            [hc.lo for hc in self.hcons]
        )

    @property
    def introduced_variables(self):
        """
        The list of the |MrsVariables| that are _introduced_ in the
        Xmrs. Introduced |MrsVariables| exist as intrinsic
        variables, labels, or holes (the HI variable of a QEQ).
        """
        return set(
            list(chain.from_iterable([(ep.iv, ep.label) for ep in self.eps]))
            + [hc.hi for hc in self.hcons]
        )

    @property
    def intrinsic_variables(self):
        """
        The list of intrinsic variables.
        """
        return list(ep.iv for ep in self.eps if not ep.is_quantifier())

    #: A synonym for :py:attr:`~delphin.mrs.xmrs.Xmrs.intrinsic_variables`
    ivs = intrinsic_variables

    @property
    def bound_variables(self):
        """
        The list of bound variables (i.e. the value of the intrinsic
        argument of quantifiers).
        """
        return list(ep.iv for ep in self.eps if ep.is_quantifier())

    #: A synonym for :py:attr:`~delphin.mrs.xmrs.Xmrs.bound_variables`
    bvs = bound_variables

    @property
    def labels(self):
        """
        The list of labels of the |EPs| in the Xmrs.
        """
        g = self._graph
        return list(set(g.node[nid]['label'] for nid in g.nodeids))
        # set(ep.label for ep in self._nid_to_ep.values()))

    @property
    def ltop(self):
        """
        The LTOP |MrsVariable|, if it exists, otherwise None.
        """
        return self.hook.ltop

    @property
    def index(self):
        """
        The INDEX |MrsVariable|, if it exists, otherwise None.
        """
        return self.hook.index

    @property
    def nodes(self):
        """
        The list of |Nodes|.
        """
        return [ep._node for ep in self.eps]
        # [copy(ep._node) for nid, ep in self._nid_to_ep.items()]

    @property
    def eps(self):
        """
        The list of |ElementaryPredications|.
        """
        g = self._graph
        return [g.node[nid]['ep'] for nid in g.nodeids]
        # copy(ep) for ep in self._nid_to_ep.values()]

    #: A synonym for :py:attr:`~delphin.mrs.xmrs.Xmrs.eps`
    rels = eps

    @property
    def args(self):
        """
        The list of all |Arguments|.
        """
        g = self._graph
        nids = g.nodeids
        return [ed['arg'] for _, _, ed in g.out_edges_iter(nids, data=True)]
        # return [arg
        #         for ep in self._nid_to_ep.values()
        #         for arg in ep.args]

    @property
    def hcons(self):
        """
        The list of all |HandleConstraints|.
        """
        return list(ed['hcons'] for _, _, ed in self._graph.edges(data=True)
                    if 'hcons' in ed)

    @property
    def links(self):
        """
        The list of |Links|.
        """
        # Return the set of links for the XMRS structure. Links exist
        # for every non-intrinsic argument that has a variable
        # that is the intrinsic variable of some other predicate,
        # as well as for label equalities when no argument link exists
        # (even considering transitivity).
        links = []
        g = self._graph
        nids = set(g.nodeids)
        labels = g.labels
        attested_eqs = defaultdict(set)
        for s, t, d in g.out_edges_iter([LTOP_NODEID] + g.nodeids, data=True):
            # if s == t or g.node[s]['ep'].iv == g.node[t]['ep'].iv:
            #     continue  # ignore ARG0s
            s_lbl = g.node[s]['label']
            if t in nids:
                t_lbl = g.node[t]['label']
                if s_lbl == t_lbl:
                    post = EQ_POST
                    attested_eqs[s_lbl].update([s, t])
                else:
                    post = NEQ_POST
            elif t in labels:
                t = self.labelset_head(t)
                if 'hcons' in d:
                    post = H_POST
                else:
                    post = HEQ_POST
            else:
                continue  # maybe log this
            links.append(Link(s, t, d.get('rargname'), post))
        # now EQ links unattested by arg links
        for lbl in g.labels:
            # I'm pretty sure this does what we want
            heads = self.labelset_head(lbl, single=False)
            if len(heads) > 1:
                first = heads[0]
                for other in heads[1:]:
                    links.append(Link(first, other, post=EQ_POST))
            # If not, this is more explicit
            # lblset = self.labelset(lbl)
            # sg = g.subgraph(lblset)
            # ns = [nid for nid, deg in sg.degree(lblset).items() if deg == 0]
            # head = self.labelset_head(lbl)
            # for n in ns:
            #     links.append(Link(head, n, post=EQ_POST))
        return sorted(links, key=lambda link: (link.start, link.end))

    # query methods
    def select_nodes(self, nodeid=None, pred=None):
        """
        Return the list of all |Nodes| that have the matching *nodeid*
        and/or *pred* values. If none match, return an empty list.
        """
        nodematch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                               (pred is None or n.pred == pred))
        return list(filter(nodematch, self.nodes))

    def select_eps(self, anchor=None, iv=None, label=None, pred=None):
        """
        Return the list of all |EPs| that have the matching *anchor*,
        *iv*, *label*, and or *pred* values. If none match, return an
        empty list.
        """
        epmatch = lambda n: ((anchor is None or n.anchor == anchor) and
                             (iv is None or n.iv == iv) and
                             (label is None or n.label == label) and
                             (pred is None or n.pred == pred))
        return list(filter(epmatch, self.eps))

    def select_args(self, anchor=None, argname=None, value=None):
        """
        Return the list of all |Arguments| that have the matching
        *anchor*, *argname*, and/or *value* values. If none match,
        return an empty list.
        """
        argmatch = lambda a: ((anchor is None or a.anchor == anchor) and
                              (argname is None or
                               a.argname.upper() == argname.upper()) and
                              (value is None or a.value == value))
        return list(filter(argmatch, self.args))

    def select_nodeids(self, iv=None, label=None, pred=None):
        g = self._graph
        nids = []
        datamatch = lambda d: ((iv is None or d['ep'].iv == iv) and
                               (pred is None or d['ep'].pred == pred) and
                               (label is None or d['label'] == label))
        for nid in g.nodeids:
            data = g.node[nid]
            if datamatch(data):
                nids.append(nid)
        return nids

    # def get_quantifier(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         if not ep.is_quantifier():
    #             return self._bv_to_nid[ep.iv]
    #     except KeyError:
    #         pass
    #     return None

    def labelset(self, label):
        return set(nx.node_boundary(self._graph, [label]))
        # alternatively:
        # return list(self._graph.adj[label].keys())

    def in_labelset(self, nids, label=None):
        if label is None:
            label = self._graph.node[next(iter(nids))]['label']
        lblset = self.labelset(label)
        return lblset.issuperset(nids)

    def labelset_head(self, label, single=True):
        g = self._graph
        lblset = self.labelset(label)
        sg = g.subgraph(lblset)
        heads = list(h for h, od in sg.out_degree(lblset).items() if od == 0)
        head_count = len(heads)
        if head_count == 0:
            raise XmrsStructureError('No head found for label {}.'
                                     .format(label))
        if not single:
            return list(map(first, sorted(sg.in_degree(heads).items(),
                                          key=second, reverse=True)))
        else:
            return max(sg.in_degree(heads).items(), key=second)[0]

    def subgraph(self, nodeids):
        g = self._graph
        labels = set(g.node[nid]['label'] for nid in nodeids)
        ivs = set(g.node[nid]['ep'].iv for nid in nodeids)
        sg = g.subgraph(chain(labels, ivs, nodeids))
        # may need some work to calculate hook or lnk here
        return Xmrs(graph=sg)

    def is_connected(self):
        return nx.is_weakly_connected(self._graph)

    def is_well_formed(self):
        """
        Return True if the Xmrs is well-formed, False otherwise.

        A well-formed Xmrs has the following properties (note, `node`
        below refers to a node in the graph, but is more like an EP than
        a DMRS Node):
          * The graph of nodes form a net (i.e. are connected).
            Connectivity can be established with variable arguments,
            QEQs, or label-equality.
          * All nodes have a label
          * The lo-handle for each QEQ must exist as the label of a node
          * All nominal nodes have a quantifier
        """
        g = self._graph
        return (
            self.is_connected() and
            all(g.node[nid].get('label', None) in g.labels
                for nid in g.nodeids) and
            all(d['qeq'].lo in g.labels
                for nid in g.nodeids
                for _, _, d in g.out_edges_iter(nid, data=True)
                if 'qeq' in d)
        )

 
    def get_nodeid(self, iv, quantifier=False):
        if iv not in self._graph:
            return None
        edge_type = 'bv' if quantifier else 'iv'
        edges = self._graph.out_edges_iter(iv, data=True)
        try:
            return next(t for _, t, d in edges if d.get(edge_type, False))
        except StopIteration:
            return None

    def get_ep(self, nodeid):
        try:
            return self._graph.node[nodeid]['ep']
        except KeyError:
            return None

    def get_node(self, nodeid):
        ep = self.get_ep(nodeid)
        node = None
        if ep is not None:
            node = ep._node
        return node

    def get_arg(self, nodeid, rargname):
        ep = self.get_ep(nodeid).get_arg(rargname)

    # def get_args(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         return ep.args
    #     except KeyError:
    #         return None

    # def get_iv(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         return ep.iv
    #     except KeyError:
    #         return None

    # def get_label(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         return ep.label
    #     except KeyError:
    #         return None

    # def get_pred(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         return ep.pred
    #     except KeyError:
    #         return None

    # def get_hcons(self, hi_var):
    #     return self._var_to_hcons.get(hi_var)

def find_argument_target(xmrs, nodeid, rargname):
    g = xmrs._graph
    tgt = next((tgt for src, tgt, data in g.out_edges_iter(nodeid, data=True)
                if data['rargname'] == rargname),
               None)
    if tgt in g.nodeids:
        return tgt
    elif tgt in g.labels:
        return xmrs.labelset_head(tgt)
    else:
        return None


def get_outbound_args(xmrs, nodeid, allow_unbound=True):
    g = xmrs._graph
    for src, tgt, data in g.out_edges_iter(nodeid, data=True):
        if src == tgt:
            continue
        if allow_unbound or tgt in g.nodeids or tgt in g.labels:
            yield data['arg']

def find_subgraphs_by_preds(xmrs, preds, connected=None):
    preds = list(preds)
    nidsets = list(
        filter(lambda ps: len(set(ps)) == len(ps),
               map(lambda p: xmrs.select_nodeids(pred=p), preds))
    )
    for sg in map(xmrs.subgraph, product(*nidsets)):
        if connected is not None and sg.is_connected() != connected:
            continue
        yield sg