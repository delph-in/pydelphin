
"""
Basic classes and functions for semantic representations.
"""

__all__ = [
    'role_priority',
    'property_priority',
    'LnkMixin',
    'Predication',
    'SemanticStructure',
    'ScopingSemanticStructure',
    'ScopeRelation',
]

from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Generic,
    Iterable,
    Mapping,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401
from delphin.lnk import Lnk

# Basic Type Aliases

Role = str
Properties = dict[str, str]  # property: value


# Functions for the default ordering of feature lists

def role_priority(role: str) -> tuple[bool, bool, str]:
    """Return a representation of role priority for ordering."""
    # canonical order: LBL ARG* RSTR BODY *-INDEX *-HNDL CARG ...
    role = role.upper()
    return (
        role != 'LBL',
        role in ('BODY', 'CARG'),
        role,
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


def property_priority(prop: str) -> tuple[int, str]:
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

class LnkMixin:
    """
    A mixin class for adding `cfrom` and `cto` properties on structures.
    """

    __slots__ = ('lnk', 'surface')

    lnk: Lnk
    surface: Optional[str]

    def __init__(
        self,
        lnk: Optional[Lnk] = None,
        surface: Optional[str] = None,
    ) -> None:
        if lnk is None:
            lnk = Lnk.default()
        self.lnk = lnk
        self.surface = surface

    @property
    def cfrom(self) -> int:
        """
        The initial character position in the surface string.

        Defaults to -1 if there is no valid cfrom value.
        """
        cfrom = -1
        try:
            if self.lnk.type == Lnk.CHARSPAN:
                cfrom = self.lnk.data[0]  # type: ignore
        except AttributeError:
            pass  # use default cfrom of -1
        return cfrom

    @property
    def cto(self) -> int:
        """
        The final character position in the surface string.

        Defaults to -1 if there is no valid cto value.
        """
        cto = -1
        try:
            if self.lnk.type == Lnk.CHARSPAN:
                cto = self.lnk.data[1]  # type: ignore
        except AttributeError:
            pass  # use default cto of -1
        return cto


# Identifiers are node ids in DMRS and EDS, or variables in MRS
# including handles and underspecified variables

Identifier = Union[str, int]
ID = TypeVar('ID', bound=Identifier)
RoleArgument = tuple[Role, ID]
ArgumentStructure = dict[ID, list[RoleArgument[ID]]]


class Predication(LnkMixin, Generic[ID], ABC):
    """
    An instance of a predicate in a semantic structure.

    While a predicate (see :mod:`delphin.predicate`) is a description
    of a possible semantic entity, a predication is the instantiation
    of a predicate in a semantic structure. Thus, multiple predicates
    with the same form are considered the same thing, but multiple
    predications with the same predicate will have different
    identifiers and, if specified, different surface alignments.
    """

    __slots__ = ('id', 'predicate', 'type', 'base')

    def __init__(self,
                 id: ID,
                 predicate: str,
                 type: Union[str, None],
                 lnk: Optional[Lnk],
                 surface: Optional[str],
                 base):
        super().__init__(lnk, surface)
        self.id = id
        self.predicate = predicate
        self.type = type
        self.base = base

    def __repr__(self):
        return '<{} object ({}:{}{}{}) at {}>'.format(
            self.__class__.__name__,
            self.id,
            self.predicate,
            str(self.lnk),
            '[{}]'.format(self.type or '?'),
            id(self))

    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...


# Structure types

P = TypeVar('P', bound=Predication)


class SemanticStructure(LnkMixin, Generic[ID, P], ABC):
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

    top: Optional[ID]
    predications: list[P]

    def __init__(
        self,
        top: Optional[ID],
        predications: Sequence[P],
        lnk: Optional[Lnk],
        surface: Optional[str],
        identifier
    ) -> None:
        super().__init__(lnk, surface)
        self.top = top
        self.predications = list(predications)
        self._pidx: dict[ID, P] = {
            p.id: p for p in predications
        }
        self.identifier = identifier

    def __repr__(self):
        return '<{} object ({}) at {}>'.format(
            self.__class__.__name__,
            ' '.join(p.predicate for p in self.predications),
            id(self))

    @abstractmethod
    def __eq__(self, other: Any) -> bool: ...

    def __contains__(self, id: Optional[ID]):
        return id in self._pidx

    def __getitem__(self, id: Optional[ID]) -> P:
        if id is None:
            raise KeyError(id)
        return self._pidx[id]

    @abstractmethod
    def arguments(self,
        types: Optional[Iterable[str]] = None,
        expressed: Optional[bool] = None,
    ) -> ArgumentStructure[ID]:
        """
        Return a mapping of the argument structure.

        Args:
            types: an iterable of predication types to include
            expressed: if `True`, only include arguments to expressed
                predications; if `False`, only include those
                unexpressed; if `None`, include both
        Returns:
            A mapping of predication ids to lists of (role, target)
            pairs for outgoing arguments for the predication.
        """
        ...

    @abstractmethod
    def properties(self, id: Optional[ID]) -> Properties:
        """Return the morphosemantic properties for *id*."""
        ...

    @abstractmethod
    def is_quantifier(self, id: Optional[ID]) -> bool:
        """Return `True` if *id* represents a quantifier."""
        ...

    @abstractmethod
    def quantification_pairs(self) -> list[tuple[Optional[P], Optional[P]]]:
        """
        Return a list of (Quantifiee, Quantifier) pairs.

        Both the Quantifier and Quantifiee are :class:`Predication`
        objects, unless they do not quantify or are not quantified by
        anything, in which case they are `None`. In well-formed and
        complete structures, the quantifiee will never be `None`.

        Example:
            >>> [(p.predicate, q.predicate)
            ...  for p, q in m.quantification_pairs()]
            [('_dog_n_1', '_the_q'), ('_bark_v_1', None)]
        """
        ...


class ScopeRelation(str, Enum):
    """The enumeration of relations used in handle constraints."""
    __str__ = str.__str__  # we want to print 'qeq', not 'ScopeRelation.qeq'

    LEQ = 'leq'              # label equality (label-to-label)
    LHEQ = 'lheq'            # label-handle equality (hole-to-label)
    OUTSCOPES = 'outscopes'  # directly or indirectly takes scope over
    QEQ = 'qeq'              # equality modulo quantifiers (hole-to-label)


ScopeLabel = str
ScopeMap = Mapping[ScopeLabel, Sequence[P]]  # input argument
Scopes = dict[ScopeLabel, list[P]]  # return value
ScopalRoleArgument = tuple[Role, ScopeRelation, ScopeLabel]
ScopalArgumentMap = Mapping[ID, Sequence[ScopalRoleArgument]]
ScopalArguments = dict[ID, list[ScopalRoleArgument]]


class ScopingSemanticStructure(SemanticStructure[ID, P], ABC):
    """
    A semantic structure that encodes quantifier scope.

    This is a base class for semantic representations, namely
    :class:`~delphin.mrs.MRS` and :class:`~delphin.dmrs.DMRS`, that
    distinguish scopal and non-scopal arguments. In addition to the
    attributes and methods of the
    :class:`~delphin.sembase.SemanticStructure` class, it also
    includes an :attr:`index` which indicates the non-scopal top of
    the structure, :meth:`scopes` for describing the labeled scopes of
    a structure, and :meth:`scopal_arguments` for describing the
    arguments that select scopes.

    Attributes:
        index: The non-scopal top of the structure.
    """

    __slots__ = ('index',)

    def __init__(
        self,
        top: Optional[ID],
        index: Optional[ID],
        predications: Sequence[P],
        lnk: Optional[Lnk],
        surface,
        identifier,
    ) -> None:
        super().__init__(top, predications, lnk, surface, identifier)
        self.index = index

    @abstractmethod
    def scopal_arguments(
        self,
        scopes: Optional[ScopeMap[P]] = None,
    ) -> ScopalArguments[ID]:
        """
        Return a mapping of the scopal argument structure.

        Unlike :meth:`SemanticStructure.arguments`, the list of
        arguments is a 3-tuple including the scopal relation: (role,
        scope_relation, scope_label).

        Args:
            scopes: mapping of scope labels to lists of predications
        """
        ...

    @abstractmethod
    def scopes(self) -> tuple[Optional[str], Scopes[P]]:
        """
        Return a tuple containing the top label and the scope map.

        The top label is the label of the top scope in the scope map.

        The scope map is a dictionary mapping scope labels to the
        lists of predications sharing a scope.
        """
        ...
