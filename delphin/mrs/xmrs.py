import logging
from operator import or_
from copy import copy, deepcopy
from collections import (OrderedDict, defaultdict)
from itertools import chain, product
import networkx as nx
from delphin._exceptions import XmrsStructureError
from delphin.mrs.ep import sort_eps
from . import (Hook, MrsVariable, ElementaryPredication, Node, Link,
               HandleConstraint, Lnk)
from .lnk import LnkMixin
from .config import (LTOP_NODEID, FIRST_NODEID,
                     ANCHOR_SORT, HANDLESORT, CVARSORT,
                     CVARG, QEQ, INTRINSIC_ARG, VARIABLE_ARG, HOLE_ARG,
                     LABEL_ARG, HCONS_ARG, CONSTANT_ARG,
                     EQ_POST, NEQ_POST, HEQ_POST, H_POST)
from .util import AccumulationDict as AccDict, XmrsDiGraph


def build_graph(hook, eps, args, hcons, icons):
    cv_to_nid = {ep.cv: ep.nodeid for ep in eps if not ep.is_quantifier()}
    # bv_to_nid = {ep.cv: ep.nodeid for ep in eps if ep.is_quantifier()}
    # lbl_to_nids = AccDict(or_, ((ep.label, {ep.nodeid}) for ep in eps))
    var_to_hcons = {hc.hi: hc for hc in hcons}
    g = XmrsDiGraph()
    g.add_node(LTOP_NODEID)
    for ep in eps:
        nid = ep.nodeid
        lbl = ep.label
        g.nodeids.append(nid)
        g.add_node(nid, {'ep': ep, 'label': lbl})
        g.add_node(lbl)
        g.add_edge(lbl, nid)
        # if not ep.is_quantifier():
        #     g.add_node(ep.cv)
        #     g.add_edge(ep.cv, ep.nodeid)
    if hook.ltop is not None:
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

    def __init__(self, hook=None, graph=None,
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

        # Inner data structures
        # self._nids = [ep.nodeid for ep in sort_eps(eps)]
        # self._nid_to_ep = OrderedDict((ep.nodeid, ep) for ep in eps)
        # self._var_to_hcons = OrderedDict((h.hi, h) for h in hcons)
        # self._var_to_icons = OrderedDict([])  # future work

        # set the proper argument types (at least distinguish label
        # equality from HCONS)
        # for ep in eps:
        #     for arg in ep.args:
        #         arg.type = arg.infer_argument_type(xmrs=self)

        # Some additional indices for quicker lookup
        # self._cv_to_nid = {ep.cv: ep.nodeid for ep in eps
        #                    if not ep.is_quantifier()}
        # self._bv_to_nid = {ep.cv: ep.nodeid for ep in eps
        #                    if ep.is_quantifier()}
        # self._label_to_nids = AccDict(
        #     or_, ((ep.label, {ep.nodeid}) for ep in eps)
        # )

        # Introduced variables are characteristic variables, labels, and
        # the hi value of HCONS. Anything else is considered to be not
        # introduced, and is probably an underspecified type (e.g. i2).
        # Note also that LTOP and INDEX are not explicitly included.
        # self._introduced_variables = set(
        #     [ep.cv for ep in eps] +
        #     [ep.label for ep in eps] +
        #     [hc.hi for hc in hcons]
        # )

        # All variables include introduced variables, LTOP and INDEX (if
        # not already included as introduced variables), all ARG vars,
        # and the lo values of HCONS.
        # self._all_variables = self._introduced_variables.union(
        #     [hook.ltop, hook.index] +
        #     [arg.value for ep in eps for arg in ep.args
        #      if isinstance(arg.value, MrsVariable)] +
        #     [hc.lo for hc in hcons]
        # )

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
        return cls(hook, graph, lnk, surface, identifier)

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
        return self.introduced_variables().union(
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
            chain.from_iterable([(ep.cv, ep.label) for ep in self.eps]) +
            [hc.hi for hc in self.hcons]
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
        links = list(self._ltop_links())
        links.extend(list(self._variable_links()))
        links.extend(list(self._eq_links(links)))
        return links

    def _ltop_links(self):
        ltop = self.ltop
        if ltop is None:
            raise StopIteration
        if ltop in self._label_to_nids:
            for target in self.label_set_heads(ltop):
                yield Link(LTOP_NODEID, target, post=HEQ_POST)
        elif ltop in self._var_to_hcons:
            for target in self.qeq_targets(ltop):
                yield Link(LTOP_NODEID, target, post=H_POST)

    def _variable_links(self):
        get_cv = self.get_cv
        for srcnid, ep in self._nid_to_ep.items():
            for arg in ep.args:
                argtype = arg.type
                var = arg.value
                if argtype == VARIABLE_ARG and var in self._cv_to_nid:
                    tgtnid = self._cv_to_nid[var]
                    if ep.label == self.get_ep(tgtnid).label:
                        post = EQ_POST
                    else:
                        post = NEQ_POST
                    tgtnids = [tgtnid]
                elif argtype == LABEL_ARG:
                    tgtnids = list(self.label_set_heads(var))
                    post = HEQ_POST
                elif argtype == HCONS_ARG:
                    tgtnids = list(self.qeq_targets(var))
                    post = H_POST
                else:
                    continue  # INTRINSIC_ARG or CONSTANT_ARG
                # special case for quantifiers
                srccv = ep.cv
                qfer_match = lambda x: get_cv(x) == srccv
                tgtqfers = list(filter(qfer_match, tgtnids))
                if len(tgtqfers) > 1:
                    logging.error('Multiple quantifiers: {}'
                                  .format(tgtqfers))
                elif len(tgtqfers) == 1:
                    tgtnids = [tgtqfers[0]]
                for tgtnid in tgtnids:
                    yield Link(srcnid, tgtnid, arg.argname, post)

    def _eq_links(self, links):
        """
        Return the list of /EQ links with no pre-slash argument name.
        These links are necessary for expressing label equality when it
        cannot be expressed through variable links. For example, in "The
        dog whose tail wagged barked", there will be an /EQ link between
        _wag_v_1 and _dog_n_1 (since they share a scope but dog is not
        an argument of wag, at least in the expected parse).
        """
        # First find the subgraphs whose label equality is given by
        # variable links.
        lbl_groups = defaultdict(lambda: defaultdict(set))
        get_label = self.get_label
        for link in filter(lambda x: x.post == EQ_POST, links):
            start = link.start
            end = link.end
            lbl = get_label(start)
            groups = lbl_groups[lbl]
            new_group = groups.get(start, {start}) | groups.get(end, {end})
            # need to update references for all in new_group
            for nid in new_group:
                lbl_groups[lbl][nid] = new_group
        # add any in a label set that aren't evidenced by links
        for lbl, nids in self._label_to_nids.items():
            groups = lbl_groups[lbl]
            for nid in nids:
                if nid not in groups:
                    groups[nid] = {nid}
        # When there's more than 1 group per label, we need /EQ links.
        # The nodes to use are selected simply by CFROM order (if
        # available).
        for lbl, groups in lbl_groups.items():
            # Change nid:set to [set] where the set is the same object
            # FIXME: this is an awful way to do it.. is there a better way?
            groups = list({id(grp): grp for grp in groups.values()}.values())
            if len(groups) < 2:
                continue
            targets = [min(grp, key=lambda x: self._nid_to_ep[x].cfrom)
                       for grp in groups]
            start = targets[0]
            for end in targets[1:]:
                yield Link(start, end, post=EQ_POST)

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

    def select_nodeids(self, pred=None, label=None):
        g = self._graph
        nids = []
        for nid in g.nodeids:
            data = g.node[nid]
            if pred is None or data['ep'].pred == pred and\
               label is None or data['label'] == label:
                nids.append(nid)
        return nids

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

    # def get_outbound_args(self, nodeid, allow_unbound=True):
    #     for arg in self.get_args(nodeid):
    #         if arg.argname == CVARG:
    #             continue
    #         if allow_unbound or arg.value in self.introduced_variables:
    #             yield arg

    # def get_quantifier(self, nodeid):
    #     try:
    #         ep = self._nid_to_ep[nodeid]
    #         if not ep.is_quantifier():
    #             return self._bv_to_nid[ep.cv]
    #     except KeyError:
    #         pass
    #     return None

    # def find_argument_targets(self, arg):
    #     argtype = arg.type
    #     var = arg.value
    #     if argtype == VARIABLE_ARG and var in self._cv_to_nid:
    #         return [self._cv_to_nid[var]]
    #     elif argtype == LABEL_ARG and var in self._label_to_nids:
    #         return self.label_set_heads(var)
    #     elif argtype == HCONS_ARG and var in self._var_to_hcons:
    #         return self.qeq_targets(var)
    #     else:
    #         return []

    # def find_argument_head(self, var):
    #     if not isinstance(var, MrsVariable):
    #         var = MrsVariable.from_string(var)
    #     if var in self._cv_to_nid:
    #         return self._cv_to_nid[var]
    #     elif var.sort == HANDLESORT:
    #         return self.find_scope_head(var)
    #     else:
    #         return None

    # def find_scope_head(self, label):
    #     nids = list(self.label_set_heads(label, resolve_hcons=True))
    #     # if there's more than one at this point, as a heuristic
    #     # look for one with a quantifier
    #     if len(nids) > 1:
    #         for nid in list(nids):
    #             if not self.get_quantifier(nid):
    #                 nids.remove(nid)
    #     assert len(nids) == 1, \
    #         'More scope heads than expected: {}'.format(
    #             ' '.join(map(str,nids)))
    #     return nids.pop()

    def label_set(self, label):
        return nx.node_boundary(self._graph, [label])

    # def label_equality_sets(self):
    #     """Return a dict of labels to the set of node ids of EPs that
    #        have that label."""
    #     return deepcopy(self._label_to_nids)

    # def label_set_heads(self, label, resolve_hcons=False):
    #     """Return the heads of a label equality set, which are the EPs
    #        with no outgoing args to other elements in the label set.
    #        Generally there is only one head, but in some (possibly
    #        incomplete) graphs there may be more than one."""
    #     if not isinstance(label, MrsVariable):
    #         label = MrsVariable.from_string(label)
    #     if resolve_hcons and label in self._var_to_hcons:
    #         # get QEQ'd label if available, else just use the label
    #         label = self._var_to_hcons[label].lo
    #     get_args = self.get_args
    #     nids = self._label_to_nids.get(label, [])
    #     for nid in nids:
    #         if not any(self._cv_to_nid.get(a.value) in nids
    #                    for a in get_args(nid)
    #                    if a.type != INTRINSIC_ARG):
    #             yield nid

    # def qeq_targets(self, handle):
    #     """Find the EP with the label QEQed from the given handle, if any."""
    #     hcons = self._var_to_hcons.get(handle)
    #     if hcons is not None:
    #         return self.label_set_heads(hcons.lo)
    #     return None

    def subgraph(self, nodeids):
        sg = self._graph.subgraph(nodeids).copy()
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

    # Manipulation methods
    # These are necessary because there is too much upkeep to just add
    # things directly to the internal data structures.

    # def add_ep(self, ep):
    #     xse = XmrsStructureError
    #     # assume the ep has a pred and label
    #     if ep.nodeid is None:
    #         ep.nodeid = max(self.nodeids) + 1
    #     nid = ep.nodeid
    #     if nid in self._nid_to_ep:
    #         raise xse('Nodeid/Anchor {} already exists.'.format(nid))
    #     is_qfer = ep.is_quantifier()
    #     cv = ep.cv
    #     if is_qfer and cv in self._bv_to_nid:
    #         raise xse('A quantifier EP with the bound variable {} already '
    #                   'exists.'.format(cv))
    #     elif not is_qfer and cv in self._cv_to_nid:
    #         raise xse('An EP with the characteristic variable {} already '
    #                   'exists.'.format(cv))

    #     self._nid_to_ep[nid] = ep
    #     # for now allowing None cvs... bad idea?
    #     if cv is not None:
    #         if is_qfer:
    #             self._bv_to_nid[cv] = nid
    #         else:
    #             self._cv_to_nid[cv] = nid
    #     self._label_to_nids.accumulate((ep.label, {nid}))
    #     self.lnk = lnk  # Lnk object (MRS-level lnk spans the whole input)

    #     # Introduced variables are characteristic variables, labels, and
    #     # the hi value of HCONS. Anything else is considered to be not
    #     # introduced, and is probably an underspecified type (e.g. i2).
    #     # Note also that LTOP and INDEX are not explicitly included.
    #     self._introduced_variables = set(
    #         [ep.cv for ep in eps] +
    #         [ep.label for ep in eps] +
    #         [hc.hi for hc in hcons]
    #     )

    #     # All variables include introduced variables, LTOP and INDEX (if
    #     # not already included as introduced variables), all ARG vars,
    #     # and the lo values of HCONS.
    #     self._all_variables = self._introduced_variables.union(
    #         [hook.ltop, hook.index] +
    #         [arg.value for ep in eps for arg in ep.args
    #          if isinstance(arg.value, MrsVariable)] +
    #         [hc.lo for hc in hcons]
    #     )
