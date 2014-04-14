import logging
from operator import add, or_
from copy import deepcopy
from collections import (OrderedDict, defaultdict)
from . import (Hook, MrsVariable, ElementaryPredication, Node, Link,
               HandleConstraint)
from .lnk import LnkMixin
from .config import (ANCHOR_SORT, HANDLESORT, CVARSORT,
                     CVARG, QEQ, VARIABLE_ARG, LTOP_NODEID,
                     EQ_POST, NEQ_POST, HEQ_POST, H_POST)
from .util import AccumulationDict, dict_of_dicts as dod

# Subclasses of Xmrs may be used for decoding.
# When encoding, only use members and methods defined in Xmrs (though
# they may be redefined in subclasses)
class Xmrs(LnkMixin):
    """Basic class for Mrs, Rmrs, and Dmrs objects."""
    def __init__(self, hook=None, nodes=None, args=None,
                 hcons=None, icons=None,
                 cvs=None, labels=None,
                 lnk=None, surface=None, identifier=None):
        """
        Xmrs objects are a middle-ground class for Mrs, Rmrs, and Dmrs.
        The structural components (ltop, index, args, hcons, and icons)
        do not use variables, but nodeids. Variables are then available
        through maps (cvs and labels) using the nodeids as keys.

        Args:
            hook (Hook): container class for things like ltop and index
            nodes: an iterable container of Nodes
            args: an iterable container of Arguments
            icons: an iterable container of IndividualConstraints
            cvs (dict): a mapping of nodeids to CVs (MrsVariables)
            labels (dict): a mapping of nodeids to labels (MrsVariables)
            lnk (Lnk): links the Xmrs to the surface form or parse structure
            surface: surface string
            identifier: discourse-utterance id
        Returns:
            an Xmrs object
        """
        # default values (or run the generators)
        nodes = list(nodes or [])
        if args is None: args = []
        if hcons is None: hcons = []
        if icons is None: icons = []
        if cvs is None: cvs = {}
        if labels is None: labels = {}

        # build inner data structures
        self.hook = hook
        # nid_to_cv includes all nodes, but cv_to_nid and bv_to_nid
        # separate them by whether the node is a quantifier
        self._nid_to_cv = OrderedDict(sorted(cvs))
        self._cv_to_nid = OrderedDict()
        self._bv_to_nid = OrderedDict()
        for node in nodes:
            nid = node.nodeid
            if node.is_quantifier():
                self._bv_to_nid[self._nid_to_cv[nid]] = nid
            else:
                self._cv_to_nid[self._nid_to_cv[nid]] = nid
        self._nid_to_label = OrderedDict(sorted(labels))
        self._label_to_nids = AccumulationDict(or_,
                                  ((lbl, {nid}) for nid, lbl in labels))
        self._nid_to_node = OrderedDict((n.nodeid, n) for n in nodes)
        self._nid_to_argmap = dod([(a.nodeid, a.argname, a) for a in args],
                                  OrderedDict)
        self._var_to_hcons = OrderedDict((h.hi, h) for h in hcons)
        self.introduced_variables = set(list(self._cv_to_nid.keys()) +\
                                        list(self._label_to_nids.keys()) +\
                                        list(self._var_to_hcons.keys()))
        self.icons  = icons # individual constraints [IndividualConstraint]
        self.lnk    = lnk   # Lnk object (MRS-level lnk spans the whole input)
        self.surface= surface   # The surface string
        self.identifier = identifier # Associates an utterance with the RMRS

        # accessor methods
        self.get_cv = self._nid_to_cv.get
        self.get_label = self._nid_to_label.get
        #self.get_pred = # needs to be defined as a method
        self.get_node = self._nid_to_node.get
        #self.get_ep # needs to be defined as a method
        self.get_argmap = self._nid_to_argmap.get
        self.get_args = lambda n: self._nid_to_argmap.get(n, {}).values()
        #self.get_links # needs to be defined as a method
        self.get_hcons = self._var_to_hcons.get

    @property
    def node_ids(self):
        # does not return LTOP nodeid
        return list(self._nid_to_node.keys())

    @property
    def anchors(self):
        # does not return LTOP anchor
        return [MrsVariable(vid=n, sort=ANCHOR_SORT) for n in self.node_ids]

    @property
    def variables(self):
        raise NotImplementedError

    @property
    def cvs(self):
        return list(self._cv_to_nid.keys())

    @property
    def labels(self):
        return list(self._label_to_nids.keys())

    @property
    def ltop(self):
        return self.hook.ltop

    @property
    def index(self):
        return self.hook.index

    @property
    def nodes(self):
        return self._nid_to_node.values()

    @property
    def eps(self):
        return [ElementaryPredication(
                    node.pred,
                    self.get_label(nid),
                    anchor=MrsVariable(vid=nid, sort=ANCHOR_SORT),
                    args=self.get_args(nid),
                    lnk=node.lnk,
                    surface=node.surface,
                    base=node.base
                )
                for nid, node in self._nid_to_node.items()]

    rels = eps # just a synonym

    @property
    def args(self):
        # _nid_to_argmap is {nid:{argname:arg}}
        return [arg for nid in self._nid_to_argmap
                    for arg in self._nid_to_argmap[nid].values()]

    @property
    def links(self):
        """Return the set of links for the XMRS structure. Links exist
           for every non-characteristic argument that has a variable
           that is the characteristic variable of some other predicate,
           as well as for label equalities when no argument link exists
           (even considering transitivity)."""
        links = list(self._variable_links())
        links.extend(list(self._eq_links(links)))
        links.extend(list(self._ltop_links()))
        return links

    def _variable_links(self):
        nid_to_cv = self._nid_to_cv
        cv_to_nid = self._cv_to_nid
        label_to_nids = self._label_to_nids
        nid_to_label = self._nid_to_label
        var_to_hcons = self._var_to_hcons
        for srcnid, argmap in self._nid_to_argmap.items():
            for arg in argmap.values():
                # ignore ARG0s
                if arg.argname == CVARG: continue
                var = arg.value
                # skip constant arguments
                if not isinstance(arg.value, MrsVariable): continue
                # variable arguments (post is EQ or NEQ)
                if var in cv_to_nid:
                    tgtnid = cv_to_nid[var]
                    if nid_to_label[srcnid] == nid_to_label[tgtnid]:
                        post = EQ_POST
                    else:
                        post = NEQ_POST
                    yield Link(srcnid, tgtnid, arg.argname, post)
                # label-equality (HEQ) or hcons (H) arguments
                else:
                    if var in label_to_nids:
                        tgtnids = list(self.label_set_heads(var))
                        post = HEQ_POST
                    elif var in var_to_hcons:
                        tgtnids = list(self.qeq_targets(var))
                        post = H_POST
                    else:
                        #TODO: log this?
                        continue
                    # special case for quantifiers
                    srccv = self._nid_to_cv[srcnid]
                    qfer_match = lambda x: nid_to_cv[x] == srccv
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
        nid_to_label = self._nid_to_label
        for link in filter(lambda x: x.post == EQ_POST, links):
            start = link.start
            end = link.end
            lbl = nid_to_label[start]
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
            if len(groups) < 2: continue
            targets = [min(grp, key=lambda x: self._nid_to_node[x].cfrom)
                       for grp in groups]
            start = targets[0]
            for end in targets[1:]:
                yield Link(start, end, post=EQ_POST)

    def _ltop_links(self):
        ltop = self.ltop
        if ltop is None: raise StopIteration
        if ltop in self._label_to_nids:
            for target in self.label_set_heads(ltop):
                yield Link(LTOP_NODEID, target, HEQ_POST)
        elif ltop in self._var_to_hcons:
            for target in self.qeq_targets(ltop):
                yield Link(LTOP_NODEID, target, H_POST)

    @property
    def hcons(self):
        return list(self._var_to_hcons.values())

    # query methods
    def select_nodes(self, nodeid=None, pred=None):
        nodematch = lambda n: ((nodeid is None or n.nodeid == nodeid) and
                               (pred is None or n.pred == pred))
        return list(filter(nodematch, self.nodes))

    def select_eps(self, anchor=None, cv=None, label=None, pred=None):
        epmatch = lambda n: ((anchor is None or n.anchor == anchor) and
                             (cv is None or n.cv == cv) and
                             (label is None or n.label == label) and
                             (pred is None or n.pred == pred))
        return list(filter(epmatch, self.eps))

    def select_args(self, anchor=None, argname=None, value=None):
        argmatch = lambda a: ((anchor is None or a.anchor == anchor) and
                              (argname is None or
                               a.argname.upper() == argname.upper()) and
                              (value is None or a.value == value))
        return list(filter(argmatch, self.args))

    def get_pred(self, nodeid):
        try:
            return self._nid_to_node[nodeid].pred
        except KeyError:
            return None

    def get_ep(self, nodeid):
        try:
            node = self._nid_to_node[nodeid]
            return ElementaryPredication(
                       node.pred,
                       self.get_label(nodeid),
                       anchor=MrsVariable(nodeid, sort=ANCHOR_SORT),
                       args=self.get_args(nodeid),
                       lnk=node.lnk,
                       surface=node.surface,
                       base=node.base,
                   )
        except KeyError:
            return None

    def get_outbound_args(self, node_id, allow_unbound=True):
        for arg in self._nid_to_argmap.get(node_id, {}).values():
            if arg.argname == CVARG:
                continue
            if allow_unbound or arg.value in self.introduced_variables:
                yield arg

    def get_quantifier(self, nid):
        cv = self._nid_to_cv.get(nid)
        try:
            return self._bv_to_nid[cv]
        except KeyError:
            return None

    def find_argument_head(self, var):
        if not isinstance(var, MrsVariable):
            var = MrsVariable.from_string(var)
        if var in self._cv_to_nids:
            return self._cv_to_nid[var]
        elif var.sort == HANDLESORT:
            return self.find_scope_head(var)
        else:
            return None

    def find_scope_head(self, label):
        nids = list(self.label_set_heads(label, resolve_hcons=True))
        # if there's more than one at this point, as a heuristic
        # look for one with a quantifier
        if len(nids) > 1:
            for nid in list(nids):
                if not self.get_quantifier(nid):
                    nids.remove(nid)
        assert len(nids) == 1, \
                'More scope heads than expected: {}'.format(' '.join(nids))
        return nids.pop()

    def arg_to_nid(self, nodeid, argname):
        """Return the node id of the EP, if any, linked by the given
           argument for the given EP."""
        var = self._nid_to_argmap.get(nodeid,{}).get(argname).value
        if var is None:
            return None
        return self._cv_to_nid.get(var)

    def label_equality_sets(self):
        """Return a dict of labels to the set of node ids of EPs that
           have that label."""
        return deepcopy(self._label_to_nids)

    def label_set_heads(self, label, resolve_hcons=False):
        """Return the heads of a label equality set, which are the EPs
           with no outgoing args to other elements in the label set.
           Generally there is only one head, but in some (possibly
           incomplete) graphs there may be more than one."""
        if not isinstance(label, MrsVariable):
            label = MrsVariable.from_string(label)
        if resolve_hcons and label in self._var_to_hcons:
            # get QEQ'd label if available, else just use the label
            label = self._var_to_hcons[label].lo
        nids = self._label_to_nids.get(label, [])
        for nid in nids:
            argmap = self._nid_to_argmap.get(nid)
            if argmap is None: continue
            for a in argmap:
                if a == CVARG: continue
            if not any(self.arg_to_nid(nid, a) in nids for a in argmap
                       if a != CVARG):
                yield nid

    def qeq_targets(self, handle):
        """Find the EP with the label QEQed from the given handle, if any."""
        hcons = self._var_to_hcons.get(handle)
        if hcons is not None:
            return self.label_set_heads(hcons.lo)
        return None