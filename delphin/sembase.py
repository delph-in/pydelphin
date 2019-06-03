
from typing import Mapping, Tuple, Dict, Union, Iterable

from delphin.lnk import Lnk, LnkMixin
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


# Basic Types

# Identifiers are node ids in DMRS and EDS, or variables in MRS
# including handles and underspecified variables
Identifier = Union[str, int]
ArgumentStructure = Mapping[Identifier, Mapping[str, Identifier]]
PropertyMap = Mapping[str, str]


# Functions for the default ordering of feature lists

def role_priority(role: str) -> Tuple[bool, bool, str]:
    """Return a representation of role priority for ordering."""
    # canonical order: LBL ARG* RSTR BODY *-INDEX *-HNDL CARG ...
    role = role.upper()
    return (
        role != 'LBL',
        role in ('BODY', 'CARG'),
        role
    )


_COMMON_PROPERTIES = (
    'PERS',      # [x] person (ERG, Jacy)
    'NUM',       # [x] number (ERG, Jacy)
    'GEND',      # [x] gender (ERG, Jacy)
    'IND',       # [x] individuated (ERG)
    'PT',        # [x] pronoun-type (ERG)
    'PRONTYPE',  # [x] pronoun-type (Jacy)
    'SF',        # [e] sentential-force (ERG)
    'TENSE',     # [e] tense (ERG, Jacy)
    'MOOD',      # [e] mood (ERG, Jacy)
    'PROG',      # [e] progressive (ERG, Jacy)
    'PERF',      # [e] perfective (ERG, Jacy)
    'ASPECT',    # [e] other aspect (Jacy)
    'PASS',      # [e] passive (Jacy)
)

_COMMON_PROPERTY_INDEX = dict((p, i) for i, p in enumerate(_COMMON_PROPERTIES))


def property_priority(prop: str) -> Tuple[int, str]:
    """
    Return a representation of property priority for ordering.

    Note:

       The ordering provided by this function was modeled on the ERG
       and Jacy grammars and may be inaccurate for others. Properties
       not known to this function will be sorted alphabetically.
    """
    index = _COMMON_PROPERTY_INDEX.get(prop.upper(), len(_COMMON_PROPERTIES))
    return (index, prop)


# Classes for Semantic Structures


class Predication(LnkMixin):
    """
    An instance of a predicate in a semantic structure.

    While a predicate (see :mod:`delphin.predicate`) is a description
    of a possible semantic entity, a predication is the instantiation
    of a predicate in a semantic structure. Thus, multiple predicates
    with the same form are considered the same thing, but multiple
    predications with the same predicate will have different
    identifiers and, if specified, different surface alignments.
    """

    __slots__ = ('id', 'predicate', 'base')

    def __init__(self,
                 id: Identifier,
                 predicate: str,
                 lnk: Lnk,
                 surface,
                 base):
        super().__init__(lnk, surface)
        self.id = id
        self.predicate = predicate
        self.base = base

    def __repr__(self):
        return '<{} object ({}:{}{}) at {}>'.format(
            self.__class__.__name__,
            self.id,
            self.predicate,
            str(self.lnk),
            id(self))


class Constraint(tuple):

    __slots__ = ()

    def __new__(cls, lhs: Identifier, relation: str, rhs: Identifier):
        return super().__new__(cls, (lhs, relation, rhs))

    def __repr__(self):
        return '<{0} object ({1[0]!s} {1[1]!s} {1[2]!s}) at {2}>'.format(
            self.__class__.__name__, self, id(self)
        )


# Structure types

Predications = Iterable[Predication]
Constraints = Iterable[Constraint]


class SemanticStructure(LnkMixin):
    """
    A basic semantic structure.

    DELPH-IN-style semantic structures are rooted DAGs with flat lists
    of predications.

    Args:
        top: identifier for the top of the structure
        predications: list of predications in the structure
        identifier: a discourse-utterance identifier
    Attributes:
        top: identifier for the top of the structure
        predications: list of predications in the structure
        identifier: a discourse-utterance identifier
    """

    __slots__ = ('top', 'predications', 'identifier', '_pidx')

    def __init__(self,
                 top: Identifier,
                 predications: Predications,
                 lnk: Lnk,
                 surface,
                 identifier):
        super().__init__(lnk, surface)
        self.top = top
        if predications is None:
            predications = []
        self.predications = predications
        self._pidx = {p.id: p for p in predications}
        self.identifier = identifier

    def __repr__(self):
        return '<{} object ({}) at {}>'.format(
            self.__class__.__name__,
            ' '.join(p.predicate for p in self.predications),
            id(self))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.top == other.top
                and self.predications == other.predications)

    def __contains__(self, id):
        return id in self._pidx

    def __getitem__(self, id):
        return self._pidx[id]

    def arguments(self, types=None) -> ArgumentStructure:
        """Return a mapping of the argument structure."""
        raise NotImplementedError()

    def properties(self, id: Identifier) -> PropertyMap:
        """Return the morphosemantic properties for *id*."""
        raise NotImplementedError()

    def is_quantifier(self, id: Identifier) -> bool:
        """Return `True` if *id* represents a quantifier."""
        raise NotImplementedError()

    def quantifier_map(self) -> Dict[Identifier, Identifier]:
        """
        Return a mapping of predication ids to quantifier ids.

        The id of every non-quantifier predication will appear as a
        key in the mapping and its value will the id of its quantifier
        if it has one, otherwise the value will be `None`.
        """
        raise NotImplementedError()
