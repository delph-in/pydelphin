
from typing import Iterable, Mapping

from delphin.lnk import Lnk, LnkMixin
from delphin.sembase import Predication, ScopingSemanticStructure
from delphin import (
    variable,
    scope
)


INTRINSIC_ROLE   = 'ARG0'
RESTRICTION_ROLE = 'RSTR'
BODY_ROLE        = 'BODY'
CONSTANT_ROLE    = 'CARG'
# the following is only used internally
_QUANTIFIER_TYPE = 'q'


class EP(Predication):
    """
    An MRS elementary predication (EP).

    EPs combine a predicate with various structural semantic
    properties. They must have a `predicate`, and `label`.  Arguments
    are optional. Intrinsic arguments (`ARG0`) are not required, but
    they are important for many semantic operations, and therefore it
    is a good idea to include them.

    Args:
        predicate: semantic predicate
        label: scope handle
        args: mapping of roles to values
        lnk: surface alignment
        surface: surface string
        base: base form
    Attributes:
        id: an identifier (same as :attr:`iv` except for quantifiers
            which replace the `iv`'s variable type with `q`)
        predicate: semantic predicate
        label: scope handle
        args: mapping of roles to values
        iv: intrinsic variable (shortcut for `args['ARG0']`)
        carg: constant argument (shortcut for `args['CARG']`)
        lnk: surface alignment
        cfrom (int): surface alignment starting position
        cto (int): surface alignment ending position
        surface: surface string
        base: base form
    """

    __slots__ = ('label', 'args')

    def __init__(self,
                 predicate: str,
                 label: str,
                 args: dict = None,
                 lnk: Lnk = None,
                 surface=None,
                 base=None):
        if args is None:
            args = {}
        # EPs formally do not have identifiers but they are very useful
        iv = args.get(INTRINSIC_ROLE)
        if RESTRICTION_ROLE in args:
            id = '{}{}'.format(_QUANTIFIER_TYPE, variable.id(iv))
        else:
            id = iv  # note: iv (and hence, id) are possibly None
        super().__init__(id, predicate, lnk, surface, base)
        self.label = label
        self.args = args
        self.base = base

    def __eq__(self, other):
        return (self.predicate == other.predicate
                and self.label == other.label
                and self.args == other.args)

    def __ne__(self, other):
        if not isinstance(other, EP):
            return NotImplemented
        return not (self == other)

    def __repr__(self):
        return '<{} object ({}:{}({})) at {}>'.format(
            self.__class__.__name__,
            self.label,
            self.predicate,
            ', '.join('{} {}'.format(role, val)
                      for role, val in self.args.items()),
            id(self))

    ## Properties interpreted from roles

    @property
    def iv(self):
        """The intrinsic argument (likely `ARG0`)."""
        return self.args.get(INTRINSIC_ROLE, None)

    @property
    def carg(self):
        """The constant argument (likely `CARG`)."""
        return self.args.get(CONSTANT_ROLE, None)

    def outgoing_args(self, variable_types=('e', 'h', 'x')):
        """A mapping of roles to outgoing arguments."""
        args = {}
        for role, arg in self.args.items():
            if role in (INTRINSIC_ROLE, CONSTANT_ROLE):
                continue
            if variable.sort(arg) in variable_types:
                args[role] = arg
        return args

    def is_quantifier(self):
        """
        Return `True` if this is a quantifier predication.
        """
        return RESTRICTION_ROLE in self.args


class HCons(object):
    """
    A relation between two handles.

    Arguments:
        hi: the higher-scoped handle
        relation: the relation of the constraint (nearly always
            `"qeq"`, but `"lheq"` and `"outscopes"` are also valid)
        lo: the lower-scoped handle
    Attributes:
        hi: the higher-scoped handle
        relation: the relation of the constraint
        lo: the lower-scoped handle
    """

    __slots__ = ('hi', 'relation', 'lo')

    QEQ = 'qeq'  # Equality modulo Quantifiers
    LHEQ = 'lheq'  # Label-Handle Equality
    OUTSCOPES = 'outscopes'  # Outscopes

    def __init__(self, hi: str, relation: str, lo: str):
        self.hi = hi
        self.relation = relation
        self.lo = lo

    def __eq__(self, other):
        return (self.hi == other.hi
                and self.relation == other.relation
                and self.lo == other.lo)

    def __ne__(self, other):
        if not isinstance(other, HCons):
            return NotImplemented
        return not (self == other)

    def __repr__(self):
        return '<HCons object ({} {} {}) at {}>'.format(
               str(self.hi), self.relation, str(self.lo), id(self)
        )

    @classmethod
    def qeq(cls, hi, lo):
        return cls(hi, HCons.QEQ, lo)


class ICons(object):
    """
    Individual Constraint: A relation between two variables.

    Arguments:
        left: intrinsic variable of the constraining EP
        relation: relation of the constraint
        right: intrinsic variable of the constrained EP
    Attributes:
        left: intrinsic variable of the constraining EP
        relation: relation of the constraint
        right: intrinsic variable of the constrained EP
    """

    __slots__ = ('left', 'relation', 'right')

    def __init__(self, left, relation, right):
        self.left = left
        self.relation = relation
        self.right = right

    def __eq__(self, other):
        return (self.left == other.left
                and self.relation == other.relation
                and self.right == other.right)

    def __ne__(self, other):
        if not isinstance(other, ICons):
            return NotImplemented
        return not (self == other)

    def __repr__(self):
        return '<ICons object ({} {} {}) at {}>'.format(
               str(self.left), self.relation, str(self.right), id(self)
        )


# class MRSFragment(object):
#     def finalize(self):
#         pass


class MRS(ScopingSemanticStructure):
    """
    A semantic representation in Minimal Recursion Semantics.

    Args:
        top: the top scope handle
        index: the top variable
        rels: iterable of EP relations
        hcons: iterable of handle constraints
        icons: iterable of individual constraints
        variables: mapping of variables to property maps
        lnk: surface alignment
        surface: surface string
        identifier: a discourse-utterance identifier
    """

    __slots__ = ('rels', 'hcons', 'icons', 'variables')

    def __init__(self,
                 top: str,
                 index: str,
                 rels: Iterable[EP],
                 hcons: Iterable[HCons],
                 icons: Iterable[ICons] = None,
                 variables: Mapping[str, Mapping[str, str]] = None,
                 lnk: Lnk = None,
                 surface=None,
                 identifier=None):

        super().__init__(self, top, index, lnk, surface, identifier)

        if rels is None:
            rels = []
        if hcons is None:
            hcons = []
        if icons is None:
            icons = []
        if variables is None:
            variables = {}

        self.rels = rels
        self.hcons = hcons
        self.icons = icons
        self.variables = _fill_variables(
            variables, top, index, rels, hcons, icons)

        # # indices for faster lookup
        # self._epidx = {ep.intrinsic_variable: ep for ep in rels
        #                if ep.intrinsic_variable is not None}
        # self._hcidx = {hc.hi: hc for hc in hcons}
        # self._icidx = {ic.left: ic for ic in icons}

    def __eq__(self, other):
        if not isinstance(other, MRS):
            return NotImplemented
        return (self.top == other.top
                and self.index == other.index
                and self.rels == other.rels
                and self.hcons == other.hcons
                and self.icons == other.icons
                and self.variables == other.variables)

    def __ne__(self, other):
        if not isinstance(other, MRS):
            return NotImplemented
        return not (self == other)

    def scopetree(self):
        """
        Return a mapping of quantifier scopes.

        Returns:
            delphin.scope.ScopeTree
        """
        scopes = {label: [ep.iv for ep in eps]
                  for label, eps in self.scopes().items()}
        _hcmap = {hc.hi: hc for hc in self.hcons}
        qeqs = []
        heqs = []
        if self.top in _hcmap:
            qeqs.append((self.top, _hcmap[self.top].lo))
        for ep in self.rels:
            for arg in ep.outgoing_args('h').values():
                if arg in scopes:
                    heqs.append(ep.label, arg)
                elif arg in _hcmap:
                    hc = _hcmap[arg]
                    assert hc.relation == HCons.QEQ
                    qeqs.append((ep.label, hc.lo))
        assert len(self.hcons) == len(qeqs)  # are all accounted for?
        return scope.ScopeTree(self.top, scopes, heqs, qeqs)

    def scopes(self):
        """Return a mapping of scope labels to EPs sharing that scope."""
        scopes = {}
        for ep in self.rels:
            scopes.setdefault(ep.label, []).append(ep)
        return scopes

    def properties(self, var):
        """Return the properties associated with variable *var*."""
        return self.variables[var]


### Helper functions

def _fill_variables(vars, top, index, rels, hcons, icons):
    if top is not None and top not in vars:
        vars[top] = {}
    if index is not None and index not in vars:
        vars[index] = {}
    for ep in rels:
        if ep.label not in vars:
            vars[ep.label] = {}
        for role, value in ep.args.items():
            if role != CONSTANT_ROLE and value not in vars:
                vars[value] = {}
    for hc in hcons:
        if hc.lo not in vars:
            vars[hc.lo] = {}
        if hc.hi not in vars:
            vars[hc.hi] = {}
    for ic in icons:
        if ic.left not in vars:
            vars[ic.left] = {}
        if ic.right not in vars:
            vars[ic.right] = {}
    return vars
