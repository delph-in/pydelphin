from collections import defaultdict
import re

##############################################################################
##############################################################################
### Main MRS classes

class Mrs(object):
    """Minimal Recursion Semantics class containing a top handle, a bag
       of ElementaryPredications, and a bag of handle constraints."""

    TOP_HANDLE = 'ltop'
    MAIN_EVENT_VAR = 'index'

    def __init__(self, ltop=None, index=None, rels=None, hcons=None,
                 link=None, surface=None, identifier=None):
        # consider enclosing ltop, ltop, index, etc. in a hook object
        # self.hook = {'ltop': ltop}
        self.ltop = ltop   # the global top handle
        self.index = index # the main event index
        # RELS and HCONS are technically unordered bags, but I use lists
        # here to keep track of order for encoding purposes. During
        # operations like MRS comparison, they should be treated as
        # unordered
        # RELS is the list of relations, or Elementary Predications
        self.rels = rels if rels is not None else []
        # HCONS is the list of handle constraints
        self.hcons = hcons if hcons is not None else []
        # MRS objects can have Links to surface structure just like
        # EPs, but it spans the whole input
        self.link = link
        # The surface form can be stored for convenience, but it
        # shouldn't affect the semantics
        self.surface = surface
        # An independent identifier can be assigned, as well
        self.identifier = identifier
        # vars should not be provided as a parameter, but taken from
        # those in index and in EPs in rels. They are unified in the
        # resolve() method.
        self._vars = {}
        self._handles = {}
        # the role map is used in isomorphism calculations, but is
        # cached here for efficiency's sake. It maps a handle or
        # variable to all the contexts it appears in, like:
        # {x4: [("_some_pred", "ARG0"), ...], ...}
        self._role_map = {}
        # resolve the structure after its properties have been assigned
        self.resolve()

    # I use properties to get the internal variables _handles and _vars
    # because, ideally, they will not be set by the user, but generated
    # automatically in a call to resolve()
    @property
    def handles(self):
        """The handles (e.g. h1, h3) used in the MRS."""
        return self._handles

    @property
    def variables(self):
        """The variables (e.g. e2, x4) used in the MRS."""
        return self._vars

    def resolve(self):
        """Using the structures that have been declared, complete the
           MRS by unifying variables (and properties), and checking for
           a valid MRS."""
        self.resolve_handles()
        self.resolve_variables()
        self.create_role_map()
        # self.validate()

    def resolve_handles(self):
        """Collect the handles used in the MRS. Since handles are just
           strings, they don't need to be resolved, but this method is
           here in case a Handle class is later defined."""
        self._handles = {}
        if self.ltop is not None:
            self._handles[self.ltop] = self.ltop
        for ep in self.rels:
            for (scargname, handle) in ep.scargs.items():
                self._handles[handle] = handle
        #NOTE: I assume all handles in HCONS should already be
        #      specified elswhere in the MRS, so I don't add them

    def resolve_variables(self):
        """Unify the variables that exist in INDEX and the EPs."""
        # variables without a name need to be compared using vid
        self._vars = {}
        if self.index is not None:
            self._vars[self.index.name] = self.index
        for ep in self.rels:
            for (argname, var) in ep.args.items():
                assert(isinstance(var, MrsVariable))
                if var.name in self._vars:
                    # If a variable already exists, unify the properties and
                    # set the second reference to the first instance
                    self.unify_var_props(var)
                    ep.args[argname] = self._vars[var.name]
                else:
                    self._vars[var.name] = var

    def unify_var_props(self, var):
        """Merge var's properties with those already stored, and raise a
           ValueError if there's a conflict. Exact-match is required."""
        if var.sort and var.sort != self._vars[var.name].sort:
            raise ValueError(str.format("Variable {0} has conflicting " +\
                                        "types: {1}, {2}", var.name,
                                        self._vars[var.name].sort, var.sort))
        for prop in var.props:
            val = var.props[prop]
            props = self._vars[var.name].props
            if props.get(prop, val) != val:
                raise ValueError(
                    str.format("Cannot set {0} property to {1}, as it is " +\
                               "already set to {2}", prop, val, props[prop]))
            else:
                props[prop] = val

    def create_role_map(self):
        """Create a mapping from each handle or predicate to the
           contexts in which they occur."""
        self._role_map = defaultdict(set)
        self._role_map[self.ltop].add(Mrs.TOP_HANDLE)
        self._role_map[self.index].add(Mrs.MAIN_EVENT_VAR)
        for ep in self.rels:
            for scarg, h in ep.scargs.items():
                self._role_map[h].add((str(ep.pred), scarg))
            for arg, v in ep.args.items():
                self._role_map[v].add((str(ep.pred), arg))

    #def ep_conjunctions(self):

    def __eq__(self, other):
        """Equality of MRSs is determined by their being isomorphic."""
        return isomorphic(self, other)

    #def __len__(self):
    #    """Return the length of the MRS, which is the number of EPs in
    #       the RELS list."""
    #    return len(self.rels)

class ElementaryPredication(object):
    """An elementary predication (EP) is a single relation."""

    def __init__(self, pred=None, label=None, scargs=None, args=None,
                 link=None, surface=None, base=None):
        self.label = label
        self.pred = pred # mrs.Pred object
        self.args = args if args is not None else {}
        self.scargs = scargs if scargs is not None else {}
        self.link = link # mrs.Link object
        self.surface = surface
        self.base = base # here for compatibility with the DTD

    def __len__(self):
        """Return the length of the EP, which is the number of args and
           scargs it contains."""
        # should this be cached?
        return len(self.args) + len(self.scargs)

    def __repr__(self):
        return 'ElementaryPredication(' + str(self.pred) + ')'

    def __str__(self):
        return self.__repr__()

sort_vid_re = re.compile(r'(\w*\D)(\d+)')
def sort_vid_split(vs):
    return sort_vid_re.match(vs).groups()

class MrsVariable(object):
    """A variable has a variable type and properties."""

    def __init__(self, name=None, vid=None, sort=None, props=None):
        self.name = name # name is the sort + vid (e.g. x4, h1)
        self.vid = vid   # vid is the number of the name (e.g. 1)
        self.sort = sort # sort is the letter(s) of the name (e.g. h)
        # Consider making _props a list if order is important
        self.props = props if props is not None else {}
        self.resolve()

    def resolve(self):
        if self.name is not None:
            _vid, _sort = sort_vid_split(self.name)
            if self.vid is None:
                self.vid = _vid
            if self.sort is None:
                self.sort is _sort
        # only create the name if both vid and sort are given
        elif self.vid is not None and self.sort is not None:
            self.name = self.sort + str(self.vid)


    def __repr__(self):
        if self.name is not None:
            return "MrsVariable(" + self.name + ")"
        else:
            return "MrsVariable(vid=" + self.vid + ")"

    def __str__(self):
        return self.__repr__()

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

class Link(object):
    # link types
    # These types determine how a link on an EP or MRS are to be interpreted,
    # and thus determine the data type/structure of the link data
    CHARSPAN  = 'charspan'  # Character span; a pair of offsets
    CHARTSPAN = 'chartspan' # Chart vertex span: a pair of indices
    TOKENS    = 'tokens'    # Token numbers: a list of indices
    EDGE      = 'edge'      # An edge identifier: a number

    def __init__(self, data, type):
        self.type = type
        # consider type-checking the data based on the type
        self.data = data

realpred_re = re.compile(r'_([^_\\]*(?:\\.[^_\\]*)*)')
class Pred(object):
    GPRED    = 'grammarpred' # only a string allowed
    REALPRED = 'realpred'    # may explicitly define lemma, pos, sense
    SPRED    = 'stringpred'  # string-form of realpred

    def __init__(self, string=None, lemma=None, pos=None, sense=None):
        # SPREDs have an internal structure (defined here:
        # http://moin.delph-in.net/RmrsPos), but basically:
        #   _lemma_pos(_sense)?_rel
        # Note that sense is optional, but the initial underscore is meaningful
        self.string = string # required for GPRED or SPRED
        # If a string is given, lemma, pos, and sense will be overwritten
        self.lemma = lemma
        self.pos = pos
        self.sense = sense
        # The type is easily inferable
        self.type = None
        self.resolve()

    def __eq__(self, other):
        if isinstance(other, Pred):
            other = other.string
        return self.string.strip('"') == other.strip('"')

    def __str__(self):
        return self.string

    def resolve(self):
        predstr = None if self.string is None else self.string.strip('"')
        if predstr is not None:
            if not predstr.lower().endswith('_rel'):
                raise ValueError('Predicate strings must end with "_rel"')
            # the easiest case is gpreds
            if not predstr.startswith('_'):
                self.type = Pred.GPRED
                self.lemma = self.pos = self.sense = None
            # string pred
            else:
                self.type = Pred.SPRED
                # _lemma_pos(_sense)?_rel
                fields = realpred_re.findall(predstr)
                if len(fields) == 3:
                    self.lemma, self.pos, _ = fields
                    self.sense = None
                elif len(fields) == 4:
                    self.lemma, self.pos, self.sense, _ = fields
                else:
                    raise ValueError('Unexpected predicate string: ' + predstr)
        elif self.lemma is not None or self.pos is not None:
            self.type = Pred.REALPRED
            if None in (self.lemma, self.pos):
                raise TypeError('If lemma is specified, pos must be ' +\
                                'specified as well.')
            toks = ['', self.lemma, self.pos]
            if self.sense is not None:
                toks += [self.sense]
            self.string = '_'.join(toks + ['rel'])

###############################################################################
###############################################################################
#### Comparison Functions

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
    with all labels, scalar args, and regular args linked to the same
    entities, and used in the same handle constraints. Variable
    properties must also be the same, but this can be ignored by
    setting the ignore_varprops parameter to True (useful when comparing
    MRSs where one has gone through a SEMI.vpm mapping).
    """
    # some simple tests to save time
    if len(mrs1.rels) != len(mrs2.rels) or\
       len(mrs1.handles) != len(mrs2.handles) or\
       len(mrs1.variables) != len(mrs2.variables) or\
       len(mrs1.hcons) != len(mrs2.hcons):
        return False
    mapping = BidirectionalMap(pairs=[(mrs1.ltop, mrs2.ltop),
                                      (mrs1.index.name, mrs2.index.name)])
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
            if v.props != v2.props:
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
            [(lhs.scargs[s], rhs.scargs[s]) for s in lhs.scargs] +\
            [(lhs.args[v].name, rhs.args[v].name) for v in lhs.args])
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
        for s in lhs.scargs:
            if mrs1._role_map[lhs.scargs[s]] != mrs2._role_map[rhs.scargs[s]]:
                return False
        for v in lhs.args:
            if mrs1._role_map[lhs.args[v]] != mrs2._role_map[rhs.args[v]]:
                return False
    except KeyError:
        return False
    return True
