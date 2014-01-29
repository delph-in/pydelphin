from collections import (OrderedDict, defaultdict)
from .lnk import LnkMixin
from .link import Link
from .hcons import HandleConstraint
from .config import (QEQ, EQ_POST)

# Subclasses of Xmrs may be used for decoding.
# When encoding, only use members and methods defined in Xmrs (though
# they may be redefined in subclasses)
class Xmrs(LnkMixin):
    """Basic class for Mrs, Rmrs, and Dmrs objects."""
    def __init__(self, hook=None, # top-level handles/variables
                 args=None,  # arguments
                 eps=None,   # ElementaryPredications
                 hcons=None, icons=None,      # handle/individual constraints
                 lnk=None, surface=None,      # surface-string attributes
                 identifier=None):            # discourse-utterance id
        self.hook = hook
        # semi-RMRS-style roles {anchor: {ROLE:TGT}}
        self.args   = OrderedDict()
        for nid, arg in args:
            (argname, tgtvar) = arg
            if nid not in self.args: self.args[nid] = OrderedDict()
            self.args[nid][argname] = tgtvar
        # eps can be DMRS-style nodes or MRS EPs; {anchor: Node}
        self.eps    = OrderedDict([(ep.nodeid, ep) for ep in (eps or [])])
        self.hcons  = hcons # handle constraints [HandleConstraint]
        self.icons  = icons # individual constraints [IndividualConstraint]
        self.lnk    = lnk   # Lnk object (MRS-level lnk spans the whole input)
        self.surface= surface   # The surface string
        self.identifier = identifier # Associates an utterance with the RMRS
        Xmrs.resolve(self) # Call explicitly so the local resolve() runs

    def resolve(self):
        # one-to-one characteristic-variable to ep map
        self.cv_map = dict((ep.cv.vid, ep) for ep in self.eps.values()
                           if not ep.is_quantifier() and ep.cv is not None)
        # one-to-many label-equality-graph
        self.label_sets = self.label_equality_sets()
        self.hcons_map = dict((h.hi, h) for h in self.hcons)
        # one-to-many ep-to-ep QEQ graph ("hole to label qeq graph")
        self.qeq_graph = defaultdict(list)
        for hc in self.hcons:
            if hc.relation != QEQ: continue
            if hc.lo.vid not in self.label_sets:
                logging.warn('QEQ lo handle is not an EP\'s LBL: {}'
                             .format(hc.lo))
            #self.qeq_graph[hc.hi] =
        #if self.index is None:
        #    self.index = self.find_head_ep().cv

    def arg_to_ep(self, nodeid, argname):
        """Return the EP, if any, linked by the given argument for the
           given EP."""
        var = self.args.get(nodeid,{}).get(argname)
        if var is None:
            return None
        return self.cv_map.get(var.vid)

    @property
    def ltop(self):
        return self.hook.ltop

    @property
    def index(self):
        return self.hook.index

    @property
    def rels(self):
        try:
            return self._rels
        except AttributeError:
            self._rels = []
            for nodeid, node in self.eps.items():
                pass
                # add arguments to args
            return self._rels

    @property
    def nodes(self):
        return self.eps.values()

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
            for srcid, argdict in self.args.items():
                for argname, tgtvar in argdict.items():
                    tgtvid = tgtvar.vid
                    if tgtvid in self.cv_map:
                        tgtid = self.cv_map[tgtvid].nodeid
                    elif tgtvid in self.label_sets:
                        tgtid = self.label_set_head(tgtvid).nodeid
                    elif tgtvar in self.hcons_map:
                        qeqtgt = self.qeq_target(tgtvar)
                        if qeqtgt is not None:
                            tgtid = self.qeq_target(tgtvar).nodeid
                        else:
                            logging.warn('QEQ lo handle is not instantiated '
                                         'in the MRS: {}'.format(
                                             self.hcons_map[tgtvar].hi))
                            continue
                    else:
                        continue #TODO: log this or something
                    post = get_dmrs_post(self, srcid, argname, tgtid)
                    if post == EQ_POST:
                        srcep = self.eps[srcid]
                        tgtep = self.eps[tgtid]
                        # first check for membership, since it can happen more
                        # than once.
                        if srcep in lbl_sets[srcep.label.vid]:
                            lbl_sets[srcep.label.vid].remove(srcep)
                        if tgtep in lbl_sets[tgtep.label.vid]:
                            lbl_sets[tgtep.label.vid].remove(tgtep)
                    self._links += [Link(srcid, tgtid, argname, post)]
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

    def label_equality_sets(self):
        """Return a list of labels to the set of EPs that
           have that label."""
        lbl_eq = defaultdict(list)
        for ep in self.eps.values():
            lbl_eq[ep.label.vid] += [ep]
        return lbl_eq

    def label_set_head(self, label_id):
        """Return the head of a label equality set, which is the first EP
           with no outgoing args to other elements in the label set."""
        lblset = self.label_sets.get(label_id, [])
        for ep in lblset:
            if not any(self.arg_to_ep(ep.nodeid, a) in lblset
                       for a in self.args.get(ep.nodeid,[])):
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
