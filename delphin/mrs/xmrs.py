import logging
from operator import add
from collections import (OrderedDict, defaultdict)
from . import (Hook, MrsVariable, ElementaryPredication, Node, Link,
               HandleConstraint)
from .lnk import LnkMixin
from .config import (ANCHOR_SORT, CVARSORT, QEQ, EQ_POST, VARIABLE_ARG)
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
        # default values
        if nodes is None: nodes = []
        if args is None: args = []
        if hcons is None: hcons = []
        if icons is None: icons = []
        if cvs is None: cvs = {}
        if labels is None: labels = {}

        # build inner data structures
        self.hook = hook
        self._nid_to_cv = OrderedDict(sorted(cvs))
        self._cv_to_nids = AccumulationDict(add,
                               ((cv, [nid]) for nid, cv in cvs))
        self._nid_to_label = OrderedDict(sorted(labels))
        self._label_to_nids = AccumulationDict(add,
                                  ((lbl, [nid]) for nid, lbl in labels))
        self._nid_to_node = OrderedDict((n.nodeid, n) for n in nodes)
        self._nid_to_argmap = dod([(a.nodeid, a.argname, a) for a in args],
                                  OrderedDict)
        self._var_to_hcons = OrderedDict((h.hi, h) for h in hcons)
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
    def nodeids(self):
        # does not return LTOP nodeid
        return list(self._nid_to_node.keys())

    @property
    def anchors(self):
        # does not return LTOP anchor
        return [MrsVariable(vid=n, sort=ANCHOR_SORT) for n in self.nodeids]

    @property
    def variables(self):
        raise NotImplementedError

    @property
    def cvs(self):
        return list(self._cv_to_nids.keys())

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
        #FIXME: remove circular import (which is why the import is here)
        from .dmrs import (Dmrs, get_dmrs_post)
        try:
            return self._links
        except AttributeError:
            lbl_sets = dict([leq for leq in self.label_equality_sets().items()
                             if len(leq[1]) > 1])
            # First get argument links
            self._links = []
            for arg in self.args:
                if not isinstance(arg.value, MrsVariable): continue
                tgtvid = arg.value.vid
                if tgtvid in self.cv_map:
                    tgtid = self.cv_map[tgtvid].nodeid
                elif tgtvid in self.label_sets:
                    tgtid = self.label_set_head(tgtvid).nodeid
                elif arg.value in self.hcons_map:
                    qeqtgt = self.qeq_target(arg.value)
                    if qeqtgt is not None:
                        tgtid = self.qeq_target(arg.value).nodeid
                    else:
                        logging.warn('QEQ lo handle is not instantiated '
                                     'in the MRS: {}'.format(
                                         self.hcons_map[arg.value].hi))
                        continue
                else:
                    continue #TODO: log this or something
                post = get_dmrs_post(self, arg.nodeid, arg.argname, tgtid)
                if post == EQ_POST:
                    srcep = self.eps[arg.nodeid]
                    tgtep = self.eps[tgtid]
                    # first check for membership, since it can happen more
                    # than once.
                    if srcep in lbl_sets.get(srcep.label,[]):
                        lbl_sets[srcep.label].remove(srcep)
                    if tgtep in lbl_sets.get(tgtep.label,[]):
                        lbl_sets[tgtep.label.vid].remove(tgtep)
                self._links += [Link(arg.nodeid, tgtid, arg.argname, post)]
            # Then label-equalities without existing variable links
            for lblid in lbl_sets:
                tgt = self.label_set_head(lblid)
                for src in lbl_sets[lblid]:
                    self._links += [Link(src.nodeid, tgt.nodeid, post=EQ_POST)]
            # LTOP link
            #TODO: should there be only 1 link? Can there be more than 1 head?
            if self.ltop is not None and self.ltop.vid in self.label_sets:
                tgt = self.label_set_head(self.ltop.vid)
                self._links += [Link(0, tgt.nodeid, post=EQ_POST)]
        return self._links

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

    def get_links(self, nodeid):
        raise NotImplementedError

    def arg_to_ep(self, nodeid, argname):
        """Return the EP, if any, linked by the given argument for the
           given EP."""
        var = self._nid_to_argmap.get(nodeid,{}).get(argname).value
        if var is None:
            return None
        return self.cv_map.get(var.vid)

    def label_equality_sets(self):
        """Return a list of labels to the set of EPs that
           have that label."""
        lbl_eq = defaultdict(list)
        for ep in self.eps:
            lbl_eq[ep.label] += [ep]
        return lbl_eq

    def label_set_head(self, label_id):
        """Return the head of a label equality set, which is the first EP
           with no outgoing args to other elements in the label set."""
        lblset = self.label_sets.get(label_id, [])
        for ep in lblset:
            if not any(self.arg_to_ep(ep.nodeid, a) in lblset
                       for a in self._nid_to_argmap.get(ep.nodeid,[])):
                return ep
        return None

    def qeq_target(self, hole):
        """Find the EP with the label QEQed from the given hole, if any."""
        hcon = self.hcons_map.get(hole)
        if hcon is not None:
            return self.label_set_head(hcon.lo.vid)
        return None

    def find_head_ep(self):
        """Return the head EP in the Xmrs. The head is defined as the EP
           with no arguments in its label group, and is not the argument
           of an EP outside of its label group."""
        candidates = set()
        # add all that have no arguments with the same label
        for nodeid, ep in self.eps.items():
            if ep.is_quantifier(): continue
            if nodeid not in self.args or\
               all(self.cv_map[var.vid].label != ep.label
                   for var in self.args[nodeid].values()
                   if var.vid in self.cv_map):
                candidates.add(nodeid)
        #print('step 1:', candidates)
        # remove those that are arguments of an EP with a different label
        #print('cvmap:', self.cv_map)
        arg_eps = lambda ep: (self.cv_map.get(v.vid)
                              for v in self.args.get(ep.nodeid,{}).values())
        for nodeid, ep in self.eps.items():
            #print('  ep:', str(nodeid), str(ep.pred))
            if ep.is_quantifier(): continue
            # consider each non-None argument
            for argep in filter(lambda x: x is not None, arg_eps(ep)):
                #print('    argep:', str(argep.nodeid), str(argep.pred))
                if argep.nodeid in candidates and argep.label != ep.label:
                    #print('   dd')
                    candidates.remove(argep.nodeid)
        #print('step 2:', candidates)
        # lastly, get rid of those in a HCONS (but consider these for LTOP)
        #print(candidates)
        #print(list(self.eps[c] for c in candidates))
        #print(self.args)
        #print(self.hcons)
        for c in list(candidates):
            #print(c, str(self.eps[c].pred))
            if c not in self.args: continue
            if any(hi in self.args[c].values() for hi in self.hcons_map.keys()):
                #print('dd')
                candidates.remove(c)
        assert(len(candidates) == 1) #TODO: log failure
        return self.eps[candidates.pop()]
