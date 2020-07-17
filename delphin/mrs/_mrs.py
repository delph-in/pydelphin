
from typing import Optional, Iterable, Mapping

from delphin.lnk import Lnk
from delphin import variable
from delphin import sembase
from delphin import scope


INTRINSIC_ROLE   = 'ARG0'
RESTRICTION_ROLE = 'RSTR'
BODY_ROLE        = 'BODY'
CONSTANT_ROLE    = 'CARG'
# the following is only used internally
_QUANTIFIER_TYPE = 'q'


class EP(sembase.Predication):
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
        self.id: str  # further constrain for EPs

        if args is None:
            args = {}
        # EPs formally do not have identifiers but they are very useful
        # note that the ARG0 may be unspecified, so use a default
        iv = args.get(INTRINSIC_ROLE, '_0')
        type, vid = variable.split(iv)
        if type == '_':
            type = None
        if RESTRICTION_ROLE in args:
            id = _QUANTIFIER_TYPE + vid
            type = None
        else:
            id = iv

        super().__init__(id, predicate, type, lnk, surface, base)
        self.label = label
        self.args = args
        self.base = base

    def __eq__(self, other):
        return (self.predicate == other.predicate
                and self.label == other.label
                and self.args == other.args)

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
        return self.args.get(INTRINSIC_ROLE, None)

    @property
    def carg(self):
        return self.args.get(CONSTANT_ROLE, None)

    def is_quantifier(self):
        """
        Return `True` if this is a quantifier predication.
        """
        return RESTRICTION_ROLE in self.args


class _Constraint(tuple):
    """
    A generic constraint between two parts of a semantic structure.
    """

    __slots__ = ()

    def __new__(cls, lhs, relation, rhs):
        return super().__new__(cls, (lhs, relation, rhs))

    def __repr__(self):
        return '<{0} object ({1[0]!s} {1[1]!s} {1[2]!s}) at {2}>'.format(
            self.__class__.__name__, self, id(self)
        )


class HCons(_Constraint):
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

    @property
    def hi(self):
        """The higher-scoped handle."""
        return self[0]

    @property
    def relation(self):
        """The constraint relation."""
        return self[1]

    @property
    def lo(self):
        """The lower-scoped handle."""
        return self[2]

    @classmethod
    def qeq(cls, hi, lo):
        return cls(hi, scope.QEQ, lo)


class ICons(_Constraint):
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

    @property
    def left(self):
        """The intrinsic variable of the constraining EP."""
        return self[0]

    @property
    def relation(self):
        """The constraint relation."""
        return self[1]

    @property
    def right(self):
        """The intrinsic variable of the constrained EP."""
        return self[2]


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

    Attributes:
        top: The top scope handle.
        index: The top variable.
        rels: The list of EPs (alias of
            :attr:`~delphin.sembase.SemanticStructure.predications`).
        hcons: The list of handle constraints.
        icons: The list of individual constraints.
        variables: A mapping of variables to property maps.
        lnk: The surface alignment for the whole MRS.
        surface: The surface string represented by the MRS.
        identifier: A discourse-utterance identifier.
    """

    __slots__ = ('hcons', 'icons', 'variables')

    def __init__(self,
                 top: str = None,
                 index: str = None,
                 rels: Iterable[EP] = None,
                 hcons: Iterable[HCons] = None,
                 icons: Iterable[ICons] = None,
                 variables: Mapping[str, Mapping[str, str]] = None,
                 lnk: Lnk = None,
                 surface=None,
                 identifier=None):

        # further constrain these types
        self.top: Optional[str]
        self.index: Optional[str]

        if rels is None:
            rels = []
        _uniquify_ids(rels)

        super().__init__(top, index, list(rels), lnk, surface, identifier)

        if hcons is None:
            hcons = []
        if icons is None:
            icons = []
        if variables is None:
            variables = {}

        self.hcons = list(hcons)
        self.icons = list(icons)
        self.variables = _fill_variables(
            variables, top, index, rels, hcons, icons)

    @property
    def rels(self):
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

    def properties(self, id):
        """
        Return the properties associated with EP *id*.

        Note that this function returns properties associated with the
        intrinsic variable of the EP whose id is *id*. To get the
        properties of a variable directly, use :attr:`variables`.
        """
        var = self[id].iv
        return self.variables[var]

    def is_quantifier(self, id):
        """Return `True` if *var* is the bound variable of a quantifier."""
        return RESTRICTION_ROLE in self[id].args

    def quantification_pairs(self):
        qmap = {ep.iv: ep
                for ep in self.rels
                if ep.is_quantifier()}
        pairs = []
        # first pair non-quantifiers to their quantifier, if any
        for ep in self.rels:
            if not ep.is_quantifier():
                pairs.append((ep, qmap.get(ep.iv)))
        # then unpaired quantifiers, if any
        for _, q in pairs:
            # some bad MRSs have multiple EPs share an ARG0; avoid the
            # KeyError by checking if they are still in qmap
            if q is not None and q.iv in qmap:
                del qmap[q.iv]
        for q in qmap.values():
            pairs.append((None, q))
        return pairs

    def arguments(self, types=None, expressed=None):
        ivs = {ep.iv for ep in self.rels}
        args = {}

        for ep in self.rels:
            id = ep.id
            args[id] = []
            for role, value in ep.args.items():
                # only outgoing arguments
                if role in (INTRINSIC_ROLE, CONSTANT_ROLE):
                    continue
                # ignore undesired argument types
                if types is not None and variable.type(value) not in types:
                    continue
                # only include expressed/unexpressed if requested
                if expressed is not None and (value in ivs) != expressed:
                    continue
                args[id].append((role, value))

        return args

    # ScopingSemanticStructure methods

    def scopes(self):
        """
        Return a tuple containing the top label and the scope map.

        Note that the top label is different from :attr:`top`, which
        is the handle that is qeq to the top scope's label. If
        :attr:`top` does not select a top scope, the `None` is
        returned for the top label.

        The scope map is a dictionary mapping scope labels to the
        lists of predications sharing a scope.
        """
        scopes = {}
        for ep in self.rels:
            scopes.setdefault(ep.label, []).append(ep)
        top = next((hc.lo for hc in self.hcons if hc.hi == self.top),
                   self.top)
        if top not in scopes:
            top = None
        return top, scopes

    def scopal_arguments(self, scopes=None):
        if scopes is None:
            # just the set of labels is enough
            scopes = {ep.label for ep in self.rels}
        hcmap = {hc.hi: hc for hc in self.hcons}
        scargs = {}

        for ep in self.rels:
            id = ep.id
            scargs[id] = []
            for role, value in ep.args.items():
                # only outgoing arguments
                if role in (INTRINSIC_ROLE, CONSTANT_ROLE):
                    continue
                # value is a label
                if value in scopes:
                    scargs[id].append((role, scope.LHEQ, value))
                # value is a hole corresponding to an hcons
                elif value in hcmap:
                    hc = hcmap[value]
                    # should the label be validated?
                    scargs[id].append((role, hc.relation, hc.lo))
                # ignore non-scopal arguments
                else:
                    continue

        return scargs


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
