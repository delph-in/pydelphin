import logging
from operator import or_
from copy import copy, deepcopy
from collections import (OrderedDict, defaultdict)
from itertools import chain, product
# consider using this:
# from functools import lru_cache
import networkx as nx
from delphin._exceptions import XmrsStructureError
from . import (Hook, MrsVariable, ElementaryPredication, Node, Link,
               HandleConstraint, Lnk)
from .lnk import LnkMixin
from .config import (LTOP_NODEID, FIRST_NODEID,
                     ANCHOR_SORT, HANDLESORT, CVARSORT,
                     CVARG, QEQ, INTRINSIC_ARG, VARIABLE_ARG, HOLE_ARG,
                     LABEL_ARG, HCONS_ARG, CONSTANT_ARG,
                     EQ_POST, NEQ_POST, HEQ_POST, H_POST)
from .util import AccumulationDict as AccDict, XmrsDiGraph, first, second


def build_graph(hook, eps, args, hcons, icons):
    cv_to_nid = {ep.cv: ep.nodeid for ep in eps if not ep.is_quantifier()}
    # bv_to_nid = {ep.cv: ep.nodeid for ep in eps if ep.is_quantifier()}
    # lbl_to_nids = AccDict(or_, ((ep.label, {ep.nodeid}) for ep in eps))
    var_to_hcons = {hc.hi: hc for hc in hcons}
    g = XmrsDiGraph()
    for ep in eps:
        nid = ep.nodeid
        lbl = ep.label
        cv = ep.cv
        g.nodeids.append(nid)
        g.labels.add(lbl)
        g.add_node(nid, {'ep': ep, 'label': lbl})
        g.add_node(lbl)
        g.add_edge(lbl, nid)
        g.add_node(cv)
        if cv in cv_to_nid:
            g.add_edge(cv, nid, {'cv': True})  # intrinsic arg
        else:
            g.add_edge(cv, nid, {'bv': True})  # quantifier
    if hook.ltop is not None:
        g.add_node(LTOP_NODEID, label=hook.ltop)
        if hook.ltop in var_to_hcons:
            hc = var_to_hcons[hook.ltop]
            g.add_edge(LTOP_NODEID, hc.lo, {'hcons': hc})
        else:
            g.add_edge(LTOP_NODEID, hook.ltop)
    for arg in args:
        nid = arg.nodeid
        attrs = {'rargname': arg.argname, 'arg': arg}
        tgt = arg.value
        if arg.type == CONSTANT_ARG:
            continue
            # g.node[ep.nodeid][arg.argname] = str(val)
        elif tgt in cv_to_nid:
            # ARG0s (including quantifiers) don't get an arg edge
            if tgt == g.node[nid]['ep'].cv:
                continue
            tgt = cv_to_nid[tgt]
        elif tgt in var_to_hcons:
            hc = var_to_hcons[tgt]
            tgt = hc.lo
            attrs['hcons'] = hc
        g.add_edge(nid, tgt, attrs)
    return g


class Xmrs(LnkMixin):
    """
    Xmrs is a common class for Mrs, Rmrs, and Dmrs objects.

    Args:
        hook: a |Hook| object to contain the ltop, xarg, and index
        eps: an iterable of |ElementaryPredications|
        hcons: an iterable of |HandleConstraints|
        icons: an iterable of IndividualConstraints (planned feature)
        lnk: the |Lnk| object associating the Xmrs to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
    """

    def __init__(self, graph=None, hook=None,
                 lnk=None, surface=None, identifier=None):
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

    @classmethod
    def from_mrs(cls, hook=None, rels=None, hcons=None, icons=None,
                 lnk=None, surface=None, identifier=None):
        eps = list(rels or [])
        # first give eps a nodeid (this is propagated to args)
        for i, ep in enumerate(eps):
            if ep.nodeid is None:
                ep.nodeid = FIRST_NODEID + i
        # then extract args
        args = chain.from_iterable(ep.args for ep in eps)
        return Xmrs.from_rmrs(hook, eps, args, hcons, icons,
                              lnk, surface, identifier)

    @classmethod
    def from_rmrs(cls, hook=None, eps=None, args=None, hcons=None, icons=None,
                  lnk=None, surface=None, identifier=None):
        if hook is None:
            hook = Hook()
        hcons = list(hcons or [])
        icons = list(icons or [])
        graph = build_graph(hook, eps, args, hcons, icons)
        # if there's no top-level lnk, get the min cfrom and max cto (if
        # not using charspan lnks, it will get -1 and -1 anyway)
        if lnk is None:
            lnk = Lnk.charspan(min([ep.cfrom for ep in eps] or [-1]),
                               max([ep.cto for ep in eps] or [-1]))
        return cls(graph, hook, lnk, surface, identifier)

    def __repr__(self):
        if self.surface is not None:
            stringform = self.surface
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
        The list of |MrsVariables|.
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
        The list of the |MrsVariables| that are introduced in the Xmrs.
        Introduced |MrsVariables| exist as characteristic variables,
        labels, or holes (the HI variable of a QEQ).
        """
        return set(
            list(chain.from_iterable([(ep.cv, ep.label) for ep in self.eps]))
            + [hc.hi for hc in self.hcons]
        )

    @property
    def characteristic_variables(self):
        """
        The list of characteristic variables.
        """
        return list(ep.cv for ep in self.eps if not ep.is_quantifier())

    #: A synonym for :py:meth:`characteristic_variables`
    cvs = characteristic_variables

    @property
    def bound_variables(self):
        """
        The list of bound variables (i.e. the value of the intrinsic
        argument of quantifiers).
        """
        return list(ep.cv for ep in self.eps if ep.is_quantifier())

    #: A synonym for :py:meth:`bound_variables`
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

    rels = eps  # just a synonym

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
        # for every non-characteristic argument that has a variable
        # that is the characteristic variable of some other predicate,
        # as well as for label equalities when no argument link exists
        # (even considering transitivity).
        links = []
        g = self._graph
        nids = set(g.nodeids)
        labels = g.labels
        attested_eqs = defaultdict(set)
        for s, t, d in g.out_edges_iter([LTOP_NODEID] + g.nodeids, data=True):
            # if s == t or g.node[s]['ep'].cv == g.node[t]['ep'].cv:
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

    def select_eps(self, anchor=None, cv=None, label=None, pred=None):
        """
        Return the list of all |EPs| that have the matching *anchor*,
        *cv*, *label*, and or *pred* values. If none match, return an
        empty list.
        """
        epmatch = lambda n: ((anchor is None or n.anchor == anchor) and
                             (cv is None or n.cv == cv) and
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

    def select_nodeids(self, cv=None, label=None, pred=None):
        g = self._graph
        nids = []
        datamatch = lambda d: ((cv is None or d['ep'].cv == cv) and
                               (pred is None or d['ep'].pred == pred) and
                               (label is None or d['label'] == label))
        for nid in g.nodeids:
            data = g.node[nid]
            if datamatch(data):
                nids.append(nid)
        return nids

    def get_outbound_args(self, nodeid, allow_unbound=True):
        g = self._graph
        for src, tgt, data in g.out_edges_iter(nodeid, data=True):
            if src == tgt:
                continue
            if allow_unbound or tgt in g.nodeids or tgt in g.labels:
                yield data['arg']

    # def get_quantifier(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         if not ep.is_quantifier():
    #             return self._bv_to_nid[ep.cv]
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
        cvs = set(g.node[nid]['ep'].cv for nid in nodeids)
        sg = g.subgraph(chain(labels, cvs, nodeids))
        # may need some work to calculate hook or lnk here
        return Xmrs(graph=sg)

    def find_subgraphs_by_preds(self, preds, connected=None):
        preds = list(preds)
        nidsets = list(
            filter(lambda ps: len(set(ps)) == len(ps),
                   map(lambda p: self.select_nodeids(pred=p), preds))
        )
        for sg in map(self.subgraph, product(*nidsets)):
            if connected is not None and sg.is_connected() != connected:
                continue
            yield sg

    def is_connected(self):
        return nx.is_weakly_connected(self._graph)

    def get_nodeid(self, cv, quantifier=False):
        if cv not in self._graph:
            return None
        edge_type = 'bv' if quantifier else 'cv'
        edges = self._graph.out_edges_iter(cv, data=True)
        try:
            return next(t for _, t, d in edges if d.get(edge_type, False))
        except StopIteration:
            return None

    # def get_ep(self, nodeid):
    #     try:
    #         return self.copy(self._nid_to_ep[nodeid])
    #     except KeyError:
    #         return None

    # def get_args(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         return ep.args
    #     except KeyError:
    #         return None

    # def get_cv(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         return ep.cv
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
