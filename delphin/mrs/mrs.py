from collections import defaultdict

##############################################################################
##############################################################################
### Main MRS classes

class Mrs(object):
    """Minimal Recursion Semantics class containing a top handle, a bag
       of ElementaryPredications, and a bag of handle constraints."""

    def __init__(self, ltop=None, index=None, rels=None, hcons=None):
        # consider enclosing ltop, ltop, index, etc. in a hook object
        # self.hook = {'ltop': ltop}
        self._ltop = ltop
        self._index = index
        # RELS and HCONS are technically unordered bags, but I use lists
        # here to keep track of order for encoding purposes. During
        # operations like MRS comparison, they should be treated as
        # unordered
        self._rels = rels if rels is not None else []
        self._hcons = hcons if hcons is not None else []
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

    @property
    def ltop(self):
        """The global top handle."""
        return self._ltop

    @ltop.setter
    def ltop(self, value):
        self._ltop = value

    @property
    def index(self):
        """The main event index."""
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

    @property
    def rels(self):
        """The bag of relations, or elementary predicates."""
        return self._rels

    @rels.setter
    def rels(self, value):
        self._rels = value

    @property
    def hcons(self):
        """The bag of handle constraints."""
        return self._hcons

    @hcons.setter
    def hcons(self, value):
        self._hcons = value

    @property
    def handles(self):
        """The handles (e.g. h1, h3) used in the MRS."""
        return self._handles

    # Maybe this shouldn't be settable.
    #@handles.setter
    #def handles(self, value):
    #    self._handles = value

    @property
    def variables(self):
        """The variables (e.g. e2, x4) used in the MRS."""
        return self._vars

    # Maybe this shouldn't be settable.
    #@variables.setter
    #def variables(self, value):
    #    self._vars = value

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
        if var.type and var.type != self._vars[var.name].type:
            raise ValueError(str.format("Variable {0} has conflicting " +\
                                        "types: {1}, {2}", var.name,
                                        self._vars[var.name].type, var.type))
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
        self._role_map[self.ltop].add('ltop')
        self._role_map[self.index].add('index')
        for ep in self.rels:
            for scarg, h in ep.scargs.items():
                self._role_map[h].add((ep.relation, scarg))
            for arg, v in ep.args.items():
                self._role_map[v].add((ep.relation, arg))

    #def ep_conjunctions(self):

    def __eq__(self, other):
        """Equality of MRSs is determined by their being isomorphic."""
        return isomorphic(self, other)

    #def __len__(self):
    #    """Return the length of the MRS, which is the number of EPs in
    #       the RELS list."""
    #    return len(self.rels)

class ElementaryPredicate(object):
    """An elementary predicate (EP) is a single relation."""

    def __init__(self, label=None, relation=None, args=None, scargs=None,
                 link=None, linktype=None):
        self._label = label
        self._relation = relation
        self._args = args if args is not None else {}
        self._scargs = scargs if scargs is not None else {}
        self._link = link
        self._linktype = linktype

    @property
    def label(self):
        """The handle of the EP."""
        return self._label

    @label.setter
    def label(self, value):
        self._label = value

    @property
    def relation(self):
        """The relation (e.g. pred name) of the EP."""
        return self._relation

    @relation.setter
    def relation(self, value):
        self._relation = value

    @property
    def args(self):
        """The list of regular arguments."""
        return self._args

    @args.setter
    def args(self, value):
        self._args = value

    @property
    def scargs(self):
        """The list of scopal arguments."""
        return self._scargs

    @scargs.setter
    def scargs(self, value):
        self._scargs = value

    # link types
    charspan_link  = 'charspan'  # Character span; a pair of offsets
    chartspan_link = 'chartspan' # Chart vertex span: a pair of indices
    tokens_link    = 'tokens'    # Token numbers: a list of indices
    edge_link      = 'edge'      # An edge identifier: a number

    @property
    def link(self):
        """The link from the predicate to the surface form. The link
           type is specified by the linktype property, and this
           determines the data type of link. For charspan and chartspan
           it will be a tuple of ints (cfrom, cto), for tokens it will
           be a list of ints [tok1, tok2, ...], and for edge it will be
           a single int."""
        return self._link

    @link.setter
    def link(self, value):
        self._link = value

    @property
    def linktype(self):
        """The type of link from a predicate to the surface form."""
        return self._linktype

    @linktype.setter
    def linktype(self, value):
        self._linktype = value

    def __len__(self):
        """Return the length of the EP, which is the number of args and
           scargs it contains."""
        # should this be cached?
        return len(self._args) + len(self._scargs)

    def __repr__(self):
        return 'ElementaryPredicate(' + self.relation + ')'

    def __str__(self):
        return self.__repr__()

class MrsVariable(object):
    """A variable has a variable type and properties."""

    def __init__(self, name=None, type=None, props=None):
        self._name = name
        self._type = type
        # Consider making _props a list if order is important
        self._props = props if props is not None else {}

    @property
    def name(self):
        """The name of the variable (e.g. x1, e2, etc)."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def type(self):
        """The type of the variable (e.g. x, e, etc)."""
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def props(self):
        """The properties of the variable (e.g. {PERS: 3})."""
        return self._props

    @props.setter
    def props(self, value):
        self._props = value

    def __repr__(self):
        return "MrsVariable(" + self._name + ")"

    def __str__(self):
        return self.__repr__()

class HandleConstraint(object):
    """A relation between two handles."""

    qeq       = 'qeq'
    lheq      = 'lheq'
    outscopes = 'outscopes'

    def __init__(self, lhandle, relation, rhandle):
        self.lhandle = lhandle
        self.relation = relation
        self.rhandle = rhandle

    def __eq__(self, other):
        return self.lhandle == other.lhandle and\
               self.relation == other.relation and\
               self.rhandle == other.rhandle

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
    if lhs.relation != rhs.relation or len(lhs) != len(rhs):
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
