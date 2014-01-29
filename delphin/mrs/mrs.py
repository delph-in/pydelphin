from collections import defaultdict
from .hook import Hook
from .var import MrsVariable
from .xmrs import Xmrs

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
        hook = Hook(ltop=ltop, index=index)
        Xmrs.__init__(self, hook, args=args, eps=rels,
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

    #def __eq__(self, other):
    #    """Equality of MRSs is determined by their being isomorphic."""
    #    return isomorphic(self, other)

    #def __len__(self):
    #    """Return the length of the MRS, which is the number of EPs in
    #       the RELS list."""
    #    return len(self.rels)
