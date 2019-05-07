
from typing import Iterable, Mapping
from operator import itemgetter

from delphin.lnk import Lnk
from delphin import variable
from delphin.sembase import (
    Predication,
    Constraint
)
from delphin import scope


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
    are optional. Intrinsic arguments (`ARG0`) are not strictly
    required, but they are important for many semantic operations, and
    therefore it is a good idea to include them.

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
        # note that the ARG0 may be unspecified, so use a default
        id = args.get(INTRINSIC_ROLE, '_0')
        if RESTRICTION_ROLE in args:
            id = _QUANTIFIER_TYPE + variable.split(id)[1]
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

    # Properties interpreted from roles

    @property
    def iv(self):
        """The intrinsic variable (namely, the value of `ARG0`)."""
        return self.args.get(INTRINSIC_ROLE, None)

    @property
    def carg(self):
        """The constant argument (namely, the value of `CARG`)."""
        return self.args.get(CONSTANT_ROLE, None)

    def is_quantifier(self):
        """
        Return `True` if this is a quantifier predication.
        """
        return RESTRICTION_ROLE in self.args


class HCons(Constraint):
    """
    A relation between two handles.

    Arguments:
        hi: the higher-scoped handle
        relation: the relation of the constraint (nearly always
            `"qeq"`, but `"lheq"` and `"outscopes"` are also valid)
        lo: the lower-scoped handle
    """

    __slots__ = ()

    def __new__(cls, hi: str, relation: str, lo: str):
        return super().__new__(cls, hi, relation, lo)

    hi = property(
        itemgetter(0), doc='the higher-scoped handle')
    relation = property(
        itemgetter(1), doc='the constraint relation')
    lo = property(
        itemgetter(2), doc='the lower-scoped handle')

    @classmethod
    def qeq(cls, hi, lo):
        return cls(hi, scope.QEQ, lo)


class ICons(Constraint):
    """
    Individual Constraint: A relation between two variables.

    Arguments:
        left: intrinsic variable of the constraining EP
        relation: relation of the constraint
        right: intrinsic variable of the constrained EP
    """

    __slots__ = ()

    def __new__(cls, left: str, relation: str, right: str):
        return super().__new__(cls, left, relation, right)

    left = property(
        itemgetter(0), doc='the intrinsic variable of the constraining EP')
    relation = property(
        itemgetter(1), doc='the constraint relation')
    right = property(
        itemgetter(2), doc='the intrinsic variable of the constrained EP')


# class MRSFragment(object):
#     def finalize(self):
#         pass


class MRS(scope.ScopingSemanticStructure):
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

    __slots__ = ('hcons', 'icons', 'variables')

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

        _uniquify_ids(rels)

        super().__init__(top, index, rels, lnk, surface, identifier)

        if hcons is None:
            hcons = []
        if icons is None:
            icons = []
        if variables is None:
            variables = {}

        self.hcons = hcons
        self.icons = icons
        self.variables = _fill_variables(
            variables, top, index, rels, hcons, icons)

    @property
    def rels(self):
        """Alias for :attr:`predications`."""
        return self.predications

    def __eq__(self, other):
        if not isinstance(other, MRS):
            return NotImplemented
        return (self.top == other.top
                and self.index == other.index
                and self.rels == other.rels
                and self.hcons == other.hcons
                and self.icons == other.icons
                and self.variables == other.variables)

    # SemanticStructure methods

    def properties(self, var):
        """Return the properties associated with variable *var*."""
        return self.variables[var]

    def is_quantifier(self, id):
        """Return `True` if *var* is the bound variable of a quantifier."""
        return RESTRICTION_ROLE in self[id].args

    def quantifier_map(self):
        """
        Return a mapping of predication ids to quantifier ids.

        The id of every non-quantifier predication will appear as a
        key in the mapping and its value will the id of its quantifier
        if it has one, otherwise the value will be `None`.

        This method only considers the bound variables of quantifiers
        and does not check that quantified EPs are in the scope of
        their quantifiers' restrictions. For well-formed MRSs this
        will not be a problem.
        """
        qs = []
        iv_to_id = {}
        qmap = {}
        for ep in self.rels:
            if ep.is_quantifier():
                qs.append(ep)
            else:
                iv_to_id[ep.iv] = ep.id
                qmap[ep.id] = None
        for ep in qs:
            id = iv_to_id.get(ep.iv)
            if id is not None:
                qmap[id] = ep.id
        return qmap

    # ScopingSemanticStructure methods

    def arguments(self, types=None, scopal=None):
        if scopal is None:
            restricted_set = set(self.variables)
        elif scopal:
            restricted_set = set(ep.label for ep in self.rels)
            restricted_set.update(hc.hi for hc in self.hcons)
        else:
            restricted_set = set(ep.iv for ep in self.rels)
        args = {}
        for ep in self.rels:
            id = ep.id
            args[id] = {}
            for role, value in ep.args.items():
                if (role not in (INTRINSIC_ROLE, CONSTANT_ROLE)
                        and (types is None or variable.type(value) in types)
                        and (value in restricted_set)):
                    args[id][role] = value
        return args

    def scope_constraints(self, scopes=None):
        # ivs = {ep.iv for ep in self.rels}
        hcmap = {hc.hi: hc for hc in self.hcons}
        labels = {ep.label for ep in self.rels}
        argstr = self.arguments(types='h')
        cons = []

        if self.top in hcmap:
            hc = hcmap[self.top]
            cons.append((self.top, hc.relation, hc.lo))

        for id, scargs in argstr.items():
            label = self[id].label
            for role, value in scargs.items():
                if value in hcmap:
                    hc = hcmap[value]
                    cons.append((label, hc.relation, hc.lo))
                elif value in labels:
                    cons.append((label, scope.LHEQ, value))
                # elif value in ivs:
                #     label2 = self[value].label
                #     if label != label2:
                #         cons.append((label2, scope.OUTSCOPES, label))
        return cons

    def scopes(self):
        """Return a mapping of scope labels to EPs sharing that scope."""
        scopes = {}
        for ep in self.rels:
            scopes.setdefault(ep.label, []).append(ep.id)
        return scopes


# Helper functions

def _uniquify_ids(rels):
    nextvid = max((variable.id(ep.iv) for ep in rels if ep.iv),
                  default=0)
    ids = set()
    for ep in rels:
        if ep.id in ids:
            ep.id = '_{}'.format(nextvid)
            nextvid += 1
        ids.add(ep.id)


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
