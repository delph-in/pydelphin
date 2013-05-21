from collections import defaultdict, OrderedDict
import logging
import re

# Contents: (search by key to jump to section)
# A0: Primary MRS classes
# A1: MRS Object classes
# A2: Comparison functions

##############################################################################
##############################################################################
### Basic MRS classes (A0)

class Lnk(object):
    # lnk types
    # These types determine how a lnk on an EP or MRS are to be interpreted,
    # and thus determine the data type/structure of the lnk data
    CHARSPAN  = 'charspan'  # Character span; a pair of offsets
    CHARTSPAN = 'chartspan' # Chart vertex span: a pair of indices
    TOKENS    = 'tokens'    # Token numbers: a list of indices
    EDGE      = 'edge'      # An edge identifier: a number

    def __init__(self, data, type):
        self.type = type
        # simple type checking
        try:
            if type == self.CHARSPAN or type == self.CHARTSPAN:
                assert(len(data) == 2)
                self.data = (int(data[0]), int(data[1]))
            elif type == self.TOKENS:
                assert(len(data) > 0)
                self.data = tuple(int(t) for t in data)
            elif type == self.EDGE:
                self.data = int(data)
            else:
                raise ValueError('Invalid lnk type: {}'.format(type))
        except (AssertionError, TypeError):
            raise ValueError('Given data incompatible with given type: ' +\
                             '{}, {}'.format(data, type))
    def __str__(self):
        if self.type == self.CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == self.CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == self.EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == self.TOKENS:
            return '<{}>'.format(' '.join(self.data))

class LnkObject(object):
    """Lnks other than CHARSPAN are rarely used, so the presence of
       cfrom and cto are often assumed. In the case that they are
       undefined, this class (and those that inherit it) gives default
       values (-1)."""
    @property
    def cfrom(self):
        if self.lnk is not None and self.lnk.type == Lnk.CHARSPAN:
            return self.lnk.data[0]
        else:
            return -1

    @property
    def cto(self):
        if self.lnk is not None and self.lnk.type == Lnk.CHARSPAN:
            return self.lnk.data[1]
        else:
            return -1

class Node(LnkObject):
    """The base class for units of MRSs containing predicates and their
       properties."""
    def __init__(self, pred, nodeid,
                 properties=None, lnk=None,
                 surface=None, base=None, carg=None):
        self.pred       = pred      # mrs.Pred object
        self.nodeid     = nodeid    # RMRS anchor, DMRS nodeid, etc.
        self.properties = properties or OrderedDict()
        self.lnk        = lnk       # mrs.Lnk object
        self.surface    = surface
        self.base       = base      # here for compatibility with the DTD
        self.carg       = carg

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Node({}[{}])'.format(self.nodeid, self.pred)

class ElementaryPredication(Node):
    """An elementary predication (EP) is an extension of a Node that
       requires a characteristic variable (cv) and label. Arguments are
       optional, so this class can be used for EPs in both MRS and RMRS."""
    def __init__(self, pred, nodeid, label, cv, args=None,
                 lnk=None, surface=None, base=None, carg=None):
        Node.__init__(self, pred, nodeid,
                      properties=cv.properties if cv is not None else None,
                      lnk=lnk, surface=surface, base=base, carg=carg)
        self.label  = label
        self.cv     = cv    # characteristic var (bound var for quantifiers)
        self.args   = args if args is not None else OrderedDict()

    def __len__(self):
        """Return the length of the EP, which is the number of args."""
        return len(self.args)

    def __repr__(self):
        return 'ElementaryPredication({}[{}])'.format(str(self.pred),
                                                      str(self.cv or '?'))

    def __str__(self):
        return self.__repr__()

    def is_quantifier(self):
        return self.pred.pos == 'q'


class MrsVariable(object):
    """A variable has a variable type and properties."""

    def __init__(self, sort, vid, properties=None):
        self.sort       = sort  # sort is the letter(s) of the name (e.g. h, x)
        self.vid        = vid   # vid is the number of the name (e.g. 1, 10003)
        if sort == 'h' and properties:
            pass # handles cannot have properties. Log this?
        self.properties = properties #TODO: consider removing properties

    def __eq__(self, other):
        try:
            return self.sort == other.sort and self.vid == other.vid
        except AttributeError:
            return False

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return 'MrsVariable({}{})'.format(self.sort, self.vid)

    def __str__(self):
        return '{}{}'.format(str(self.sort), str(self.vid))

class HandleConstraint(object):
    """A relation between two handles."""

    QEQ       = 'qeq'
    LHEQ      = 'lheq'
    OUTSCOPES = 'outscopes'

    def __init__(self, lhandle, relation, rhandle):
        self.lhandle = lhandle
        self.relation = relation
        self.rhandle = rhandle

    def __eq__(self, other):
        return self.lhandle == other.lhandle and\
               self.relation == other.relation and\
               self.rhandle == other.rhandle

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return 'HandleConstraint({})'.format(
               ' '.join([str(self.lhandle), self.relation, str(self.rhandle)]))

    def __str__(self):
        return self.__repr__()

pred_re = re.compile(r'_?(?P<lemma>.*?)_' # match until last 1 or 2 parts
                     r'((?P<pos>[a-z])_)?' # pos is always only 1 char
                     r'((?P<sense>([^_\\]|(?:\\.))+)_)?' # no unescaped _s
                     r'(?P<end>rel(ation)?)', # NB only _rel is valid
                     re.IGNORECASE)
class Pred(object):
    GPRED    = 'grammarpred' # only a string allowed
    REALPRED = 'realpred'    # may explicitly define lemma, pos, sense
    SPRED    = 'stringpred'  # string-form of realpred

    def __init__(self, string=None, lemma=None, pos=None, sense=None):
        """Extract the lemma, pos, and sense (if applicable) from a pred
           string, if given, or construct a pred string from those
           components, if they are given. Treat malformed pred strings
           as simple preds without extracting the components."""
        # GPREDs and SPREDs are given by strings (with or without quotes).
        # SPREDs have an internal structure (defined here:
        # http://moin.delph-in.net/RmrsPos), but basically:
        #   _lemma_pos(_sense)?_rel
        # Note that sense is optional. The initial underscore is meaningful.
        if string is not None:
            self.string = string
            string = string.strip('"\'')
            self.type = Pred.SPRED if string.startswith('_') else Pred.GPRED
            self.lemma, self.pos, self.sense, self.end =\
                    self.decompose_pred_string(string.strip('"\''))
        # REALPREDs are specified by components, not strings
        else:
            self.type = None
            self.lemma = lemma
            self.pos = pos
            # str(sense) in case an int is given
            self.sense = str(sense) if sense is not None else None
            # end defaults to (and really should always be) _rel
            self.end = 'rel'
            string_tokens = filter(bool, [lemma, pos, self.sense, self.end])
            self.string = '_'.join([''] + string_tokens)

    def __eq__(self, other):
        if isinstance(other, Pred):
            other = other.string
        return self.string.strip('"\'') == other.strip('"\'')

    def __repr__(self):
        return self.string

    def decompose_pred_string(self, predstr):
        """Extract the components from a pred string and log errors
           for any malformedness."""
        if not predstr.lower().endswith('_rel'):
            logging.warn('Predicate does not end in "_rel": {}'.format(predstr))
        match = pred_re.search(predstr)
        if match is None:
            logging.warn('Unexpected predicate string: {}'.format(predstr))
            return (predstr, None, None, None)
        # _lemma_pos(_sense)?_end
        return (match.group('lemma'), match.group('pos'),
                match.group('sense'), match.group('end'))

class Link(object):
    """DMRS-style Links are a way of representing arguments without
       variables. A Link encodes a start and end node, the argument
       name, and label information (e.g. label equality, qeq, etc)."""
    def __init__(self, start, end, argname=None, post=None):
        self.start    = start
        self.end      = end
        self.argname = argname
        self.post     = post

    def __repr__(self):
        return 'Link({} -> {}, {}/{})'.format(self.start, self.end,
                                              self.argname, self.post)

##############################################################################
##############################################################################
### Convenience Functions and Classes (A1a)

sort_vid_re = re.compile(r'(\w*\D)(\d+)')
def sort_vid_split(vs):
    return sort_vid_re.match(vs).groups()

def qeq(hi, lo):
    return HandleConstraint(hi, HandleConstraint.QEQ, lo)

def get_dmrs_post(xmrs, nid1, argname, nid2):
    node2lbl = xmrs.eps[nid2].label
    if xmrs.eps[nid1].label == node2lbl:
        post = Dmrs.EQ
    elif xmrs.args.get(nid1,{}).get(argname) == node2lbl:
        post = Dmrs.HEQ
    else:
        hcon = xmrs.hcons_map.get(xmrs.args.get(nid1,{}).get(argname))
        if hcon is not None and hcon.rhandle == node2lbl:
            post = Dmrs.H
        else:
            post = Dmrs.NEQ
    return post

class VarFactory(object):
    """Simple class to produce MrsVariables, incrementing the vid for
       each one."""

    def __init__(self, starting_vid=0):
        self.vid = starting_vid

    def new(self, sort, properties=None):
        self.vid += 1
        return MrsVariable(sort, self.vid-1, properties=properties)

##############################################################################
##############################################################################
### MRS object classes (A1)

# Subclasses of Xmrs may be used for decoding.
# When encoding, only use members and methods defined in Xmrs (though
# they may be redefined in subclasses)
class Xmrs(LnkObject):
    """Basic class for Mrs, Rmrs, and Dmrs objects."""
    def __init__(self, ltop=None, index=None, # top-level handles/variables
                 args=None,  # arguments
                 eps=None,   # ElementaryPredications
                 hcons=None, icons=None,      # handle/individual constraints
                 lnk=None, surface=None,      # surface-string attributes
                 identifier=None):            # discourse-utterance id
        self.ltop   = ltop  # the global top handle
        self.index  = index # the main event index
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
        self.hcons_map = dict((h.lhandle, h) for h in self.hcons)
        # one-to-many ep-to-ep QEQ graph ("hole to label qeq graph")
        self.qeq_graph = defaultdict(list)
        for hc in self.hcons:
            if hc.relation != HandleConstraint.QEQ: continue
            if hc.rhandle.vid not in self.label_sets:
                logging.warn('QEQ lo handle is not an EP\'s LBL: {}'
                             .format(hc.rhandle))
            #self.qeq_graph[hc.lhandle] =
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
                                             self.hcons_map[tgtvar].lhandle))
                            continue
                    else:
                        continue #TODO: log this or something
                    post = get_dmrs_post(self, srcid, argname, tgtid)
                    if post == Dmrs.EQ:
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
                    self._links += [Link(src.nodeid, tgt.nodeid, post=Dmrs.EQ)]
            # LTOP link
            #TODO: should there be only 1 link? Can there be more than 1 head?
            if self.ltop is not None and self.ltop.vid in self.label_sets:
                tgt = self.label_set_head(self.ltop.vid)
                self._links += [Link(0, tgt.nodeid, post=Dmrs.EQ)]
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
            return self.label_set_head(hcon.rhandle.vid)
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

class Mrs(Xmrs):
    """Minimal Recursion Semantics class containing a top handle, a bag
       of ElementaryPredications, and a bag of handle constraints."""

    TOP_HANDLE = 'ltop'
    MAIN_EVENT_VAR = 'index'

    def __init__(self, ltop=None, index=None,
                 rels=None, hcons=None, icons=None,
                 lnk=None, surface=None, identifier=None):
        # roles are embedded in EPs for MRS
        args = [(ep.nodeid, arg) for ep in rels for arg in ep.args.items()]
        Xmrs.__init__(self, ltop, index, args=args, eps=rels,
                      hcons=hcons, icons=icons,
                      lnk=lnk, surface=surface, identifier=identifier)
        # store these so the rels() method can find them
        self._rels = rels
        # vars should not be provided as a parameter, but taken from
        # those in index and in EPs in rels. They are unified in the
        # resolve() method.
        self._vars = {}
        # the role map is used in isomorphism calculations, but is
        # cached here for efficiency's sake. It maps a handle or
        # variable to all the contexts it appears in, like:
        # {x4: [("_some_pred", "ARG0"), ...], ...}
        self._role_map = {}
        # map the characteristic variables to the EPs
        self._cp_ep_map = {}
        # resolve the structure after its properties have been assigned
        self.resolve()

    # I use Python properties to get the internal variables _vars
    # because, ideally, they will not be set by the user, but generated
    # automatically in a call to resolve()
    @property
    def variables(self):
        """The variables (e.g. h1, e2, x4) used in the MRS."""
        return self._vars

    def resolve(self):
        """Using the structures that have been declared, complete the
           MRS by unifying variables (and properties), and checking for
           a valid MRS."""
        self.resolve_variables()
        self.resolve_eps()
        self.create_role_map()
        # self.validate()

    def resolve_variables(self):
        """Unify the variables that exist in LTOP, INDEX, EPs, and HCONS."""
        self._vars = {}
        def unify_var(var, ep):
            assert(isinstance(var, MrsVariable))
            if var.vid in self._vars:
                # If a variable already exists, unify the properties and
                # set the second reference to the first instance
                self.unify_var_props(var)
                var = self._vars[var.vid]
            else:
                self._vars[var.vid] = var
            return var
        if self.ltop is not None:
            self._vars[self.ltop.vid] = self.ltop
        if self.index is not None:
            self._vars[self.index.vid] = self.index
        for ep in self.rels:
            self._vars[ep.label.vid] = ep.label
            if ep.cv is not None:
                ep.cv = unify_var(ep.cv, ep)
            else:
                logging.warn('{} does not have a characteristic variable.'
                             .format(str(ep)))
            for (argname, var) in ep.args.items():
                ep.args[argname] = unify_var(var, ep)

    def unify_var_props(self, var):
        """Merge var's properties with those already stored, and raise a
           ValueError if there's a conflict. Exact-match is required."""
        if var is None: return
        vid = var.vid
        if self._vars[vid].sort is None:
            self._vars[vid].sort = var.sort
        elif var.sort != self._vars[vid].sort:
            raise ValueError("Variable {0} has conflicting types: {1}, {2}"
                             .format(vid, self._vars[vid].sort, var.sort))
        for prop in var.properties:
            val = var.properties[prop]
            props = self._vars[vid].properties
            if props.get(prop, val) != val:
                raise ValueError(
                    str.format("Cannot set {0} property to {1}, as it is " +\
                               "already set to {2}", prop, val, props[prop]))
            else:
                props[prop] = val

    def resolve_eps(self):
        """Associate an EPs properties to those of its characteristic
           variable."""
        for ep in self.rels:
            if ep.cv is not None and isinstance(ep.cv, MrsVariable):
                ep.properties = ep.cv.properties or None

    def create_role_map(self):
        """Create a mapping from each handle or predicate to the
           contexts in which they occur."""
        self._role_map = defaultdict(set)
        self._role_map[self.ltop.vid].add(Mrs.TOP_HANDLE)
        self._role_map[self.index.vid].add(Mrs.MAIN_EVENT_VAR)
        for ep in self.rels:
            for arg, v in ep.args.items():
                self._role_map[v.vid].add((str(ep.pred), arg))

    #def ep_conjunctions(self):

    def __eq__(self, other):
        """Equality of MRSs is determined by their being isomorphic."""
        return isomorphic(self, other)

    #def __len__(self):
    #    """Return the length of the MRS, which is the number of EPs in
    #       the RELS list."""
    #    return len(self.rels)

class Dmrs(Xmrs):
    EQ       = 'EQ'
    HEQ      = 'HEQ'
    NEQ      = 'NEQ'
    H        = 'H'
    CVARSORT = 'cvarsort'

    def __init__(self, ltop=None, index=None,
                 nodes=None, links=None,
                 lnk=None, surface=None, identifier=None):
        """Creating a DMRS object requires a bit of maintenance.
           Variables must be created for the labels and characteristic
           variables, and links must be converted to arguments."""
        self._links = links
        # now create necessary structure for making an Xmrs object. This is
        # essentially the same process as converting DMRS to RMRS
        vfac = VarFactory()
        # find common labels
        lbls = {}
        for l in links:
            if l.post == Dmrs.EQ:
                lbl = lbls.get(l.start) or lbls.get(l.end) or vfac.new('h')
                lbls[l.start] = lbls[l.end] = lbl
        # create any remaining uninstantiated labels
        for n in nodes:
            if n.nodeid not in lbls:
                lbls[n.nodeid] = vfac.new('h')
        # create characteristic variables (and bound variables)
        cvs = dict([(n.nodeid, vfac.new(n.properties.get(Dmrs.CVARSORT,'h'),
                                        n.properties or None)) for n in nodes])
        # convert links to args and hcons
        hcons = []
        args = []
        for l in links:
            if l.post == Dmrs.H or l.post == None:
                hole = vfac.new('h')
                hcons += [qeq(hole, lbls[l.end])]
                args += [(l.start, (l.argname, hole))]
            elif l.post == Dmrs.HEQ:
                args += [(l.start, (l.argname, lbls[l.end]))]
            else: # Dmrs.NEQ or Dmrs.EQ
                args += [(l.start, (l.argname, cvs[l.end]))]
        # "upgrade" nodes to EPs
        eps = [ElementaryPredication(n.pred, n.nodeid, lbls[n.nodeid],
                                     cvs[n.nodeid], args=None,
                                     lnk=n.lnk, surface=n.surface,
                                     base=n.base, carg=n.carg)
               for n in nodes]
        # TODO: icons not implemented yet
        icons = None
        # Finally, initialize the Xmrs using the converted structures
        Xmrs.__init__(self, ltop, index, args=args, eps=eps,
                      hcons=hcons, icons=icons,
                      lnk=lnk, surface=surface, identifier=identifier)

###############################################################################
###############################################################################
#### Comparison Functions (A2)

class BidirectionalMap(object):
    """
    Class for a bi-directional mapping the MRS variables of two MRSs.
    Used in isomorphism calculations.
    """

    def __init__(self, pairs=None):
        self._lr = {} # left to right mapping (mrs1 to mrs2)
        self._rl = {} # right to left mapping (mrs2 to mrs1)
        if pairs:
            for (lvar, rvar) in pairs:
                self.add(lvar, rvar)

    def __eq__(self, other):
        try:
            # since we ensure rl mappings don't violate lr mappings,
            # just check one side for equality.
            return self._lr == other._lr
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def add(self, lvar, rvar):
        # don't add a mapping if it violates a previous mapping
        if (lvar in self._lr and self._lr[lvar] != rvar) or \
           (rvar in self._rl and self._rl[rvar] != lvar):
            raise KeyError
        # otherwise map both directions
        self._lr[lvar] = rvar
        self._rl[rvar] = lvar

    def mapped(self, lvar, rvar):
        # We only need to check one direction
        return lvar in self._lr and self._lr[lvar] == rvar

    def pairs(self):
        return list(self._lr.items())

def isomorphic(mrs1, mrs2, ignore_varprops=False):
    """
    Given another MRS, return True if the two MRSs are isomorphic,
    otherwise return False. Isomorphism is when the MRSs share the same
    structure, including all nodes and arcs. In other words, while
    handle and variable names may be different, there is a mapping of
    the handles and variables such that the two MRSs have the same EPs
    with all labels and arguments linked to the same
    entities, and used in the same handle constraints. Variable
    properties must also be the same, but this can be ignored by
    setting the ignore_varprops parameter to True (useful when comparing
    MRSs where one has gone through a SEMI.vpm mapping).
    """
    # some simple tests to save time
    if len(mrs1.rels) != len(mrs2.rels) or\
       len(mrs1.variables) != len(mrs2.variables) or\
       len(mrs1.hcons) != len(mrs2.hcons):
        return False
    mapping = BidirectionalMap(pairs=[(mrs1.ltop, mrs2.ltop),
                                      (mrs1.index.vid, mrs2.index.vid)])
    # For RELS, sort them by length so we map those with the fewest
    # attributes first
    mapping = isomorphic_rels(mrs1, mrs2,
                              sorted(mrs1.rels, key=len),
                              sorted(mrs2.rels, key=len),
                              mapping)
    if mapping is None:
        return False
    # We know mrs1 and mrs2 have the same number of HCONS, but now
    # we that we have a mapping we can check that they are the same
    mapped_hcons1 = set((mapping._lr[h.lhandle], h.relation,
                         mapping._lr[h.rhandle])
                        for h in mrs1.hcons)
    hcons2 = set((h.lhandle, h.relation, h.rhandle) for h in mrs2.hcons)
    if mapped_hcons1 != hcons2:
        return False
    # Checking variable properties should be easy with a mapping, as
    # long as we aren't doing SEMI conversions
    if not ignore_varprops:
        for k, v in mrs1.variables.items():
            v2 = mrs2.variables[mapping._lr[k]]
            if v.properties != v2.properties:
                return False
    return True

def isomorphic_rels(mrs1, mrs2, lhs_rels, rhs_rels, mapping):
    """
    Return a valid mapping of handles and variables, if it exists, for
    the RELS lists of two given MRSs.
    """
    # base condition: map_vars returned None or there are no more rels
    if mapping is None:
        return None
    if len(lhs_rels) == len(rhs_rels) == 0:
        return mapping
    # Otherwise look for valid mappings
    lhs = lhs_rels[0]
    for i, rhs in enumerate(rhs_rels):
        if not validate_eps(mrs1, mrs2, lhs, rhs):
            continue
        # with a valid varmap, assume it is correct and recursively
        # find mappings for the rest of the variables
        new_mapping = isomorphic_rels(mrs1, mrs2,
                                      lhs_rels[1:],
                                      rhs_rels[:i] + rhs_rels[i+1:],
                                      map_vars(lhs, rhs, mapping))
        # return the first valid varmap and break out of the loop
        if new_mapping is not None:
            return new_mapping
    return None

def map_vars(lhs, rhs, mapping):
    """ If the variables in lhs and rhs are consistent with those in
        mapping, return a new mapping including those from all three."""
    try:
        new_mapping = BidirectionalMap(mapping.pairs() +\
            [(lhs.label, rhs.label)] +\
            [(lhs.args[v].vid, rhs.args[v].vid) for v in lhs.args])
        return new_mapping
    except KeyError:
        pass
    return None

def validate_eps(mrs1, mrs2, lhs, rhs):
    """
    Return True if the two EPs can be mapped. Being mappable
    means that the rels have the same length and every variable
    appears in the same set of EPs in the same attributes. For
    instance, if lhs's ARG0 is x1 and rhs's ARG0 is x2, and x1 has a
    role_map of {'dog_n_rel':'ARG0', 'the_q_rel':'ARG0',
    'bark_v_rel':'ARG1'}, then x2 must also have the same role_map
    in order to be mappable. This property must apply to all
    attributes in both EPs.
    """
    if lhs.pred != rhs.pred or len(lhs) != len(rhs):
        return False
    try:
        for v in lhs.args:
            if mrs1._role_map[lhs.args[v]] != mrs2._role_map[rhs.args[v]]:
                return False
    except KeyError:
        return False
    return True
