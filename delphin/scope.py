"""
Structures and operations for quantifier scope in DELPH-IN semantics.
"""

from __future__ import annotations

__all__ = [
    "ScopeError",
    "conjoin",
    "descendants",
    "representatives",
    # below for backward compatibility
    "LEQ",
    "LHEQ",
    "OUTSCOPES",
    "QEQ",
    "ScopingSemanticStructure",
]

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Optional,
    TypeVar,
    overload,
)

from delphin.__about__ import __version__  # noqa: F401
from delphin.exceptions import PyDelphinException
from delphin.sembase import (
    Identifier,
    Predication,
    ScopalArgumentMap,
    ScopeLabel,
    ScopeMap,
    Scopes,
    ScopingSemanticStructure,
)
from delphin.util import _connected_components

if TYPE_CHECKING:
    from delphin import dmrs, mrs


# Type Aliases

ID = TypeVar('ID', bound=Identifier)
P = TypeVar('P', bound=Predication)

Descendants = dict[ID, list[P]]
ScopeEqualities = Iterable[tuple[ScopeLabel, ScopeLabel]]
PredicationPriority = Callable[[P], Any]  # Any should be sortable


# Exceptions

class ScopeError(PyDelphinException):
    """Raised on invalid scope operations."""


# Module Functions

@overload
def conjoin(scopes: ScopeMap[mrs.EP], leqs: ScopeEqualities) -> Scopes[mrs.EP]:
    ...

@overload
def conjoin(
    scopes: ScopeMap[dmrs.Node], leqs: ScopeEqualities
) -> Scopes[dmrs.Node]:
    ...

def conjoin(scopes: ScopeMap, leqs: ScopeEqualities) -> ScopeMap:
    """
    Conjoin multiple scopes with equality constraints.

    Args:
        scopes: a mapping of scope labels to predications
        leqs: a list of pairs of equated scope labels
    Returns:
        A mapping of the labels to the predications of each conjoined
        scope. The conjoined scope labels are taken arbitrarily from
        each equated set).
    Example:
        >>> conjoined = scope.conjoin(mrs.scopes(), [('h2', 'h3')])
        >>> {lbl: [p.id for p in ps] for lbl, ps in conjoined.items()}
        {'h1': ['e2'], 'h2': ['x4', 'e6']}
    """
    scopemap: dict[ScopeLabel, list[Predication]] = {}
    for component in _connected_components(list(scopes), leqs):
        chosen_label = next(iter(component))
        scopemap[chosen_label] = []
        for label in component:
            scopemap[chosen_label].extend(scopes[label])
    return scopemap


def descendants(
    x: ScopingSemanticStructure[ID, P],
    scopes: Optional[ScopeMap[P]] = None,
) -> Descendants[ID, P]:
    """
    Return a mapping of predication ids to their scopal descendants.

    Args:
        x: an MRS or a DMRS
        scopes: a mapping of scope labels to predications
    Returns:
       A mapping of predication ids to lists of predications that are
       scopal descendants.
    Example:
        >>> m = mrs.MRS(...)  # Kim didn't think that Sandy left.
        >>> descendants = scope.descendants(m)
        >>> for id, ds in descendants.items():
        ...     print(m[id].predicate, [d.predicate for d in ds])
        ...
        proper_q ['named']
        named []
        neg ['_think_v_1', '_leave_v_1']
        _think_v_1 ['_leave_v_1']
        _leave_v_1 []
        proper_q ['named']
        named []

    """
    if scopes is None:
        _, scopes = x.scopes()
    scargs = x.scopal_arguments(scopes=scopes)
    descs: dict[ID, list[P]] = {}
    for p in x.predications:
        _descendants(descs, p.id, scargs, scopes)
    return descs


def _descendants(
    descs: dict[ID, list[P]],
    id: ID,
    scargs: ScopalArgumentMap[ID],
    scopes: ScopeMap[P],
) -> None:
    if id in descs:
        return
    descs[id] = []
    for _role, _relation, label in scargs[id]:
        assert isinstance(label, str)
        for p in scopes.get(label, []):
            descs[id].append(p)
            _descendants(descs, p.id, scargs, scopes)
            descs[id].extend(descs[p.id])


@overload
def representatives(
    x: mrs.MRS,
    priority: Optional[PredicationPriority[mrs.EP]] = None,
) -> Scopes[mrs.EP]:
    ...

@overload
def representatives(
    x: dmrs.DMRS,
    priority: Optional[PredicationPriority[dmrs.Node]] = None,
) -> Scopes[dmrs.Node]:
    ...

def representatives(
    x: ScopingSemanticStructure,
    priority: Optional[PredicationPriority] = None,
) -> ScopeMap:
    """
    Find the scope representatives in *x* sorted by *priority*.

    When predications share a scope, generally one takes another as a
    non-scopal argument. For instance, the ERG analysis of a phrase
    like "very old book" has the predicates `_very_x_deg`, `_old_a_1`,
    and `_book_n_of` which all share a scope, where `_very_x_deg`
    takes `_old_a_1` as its `ARG1` and `_old_a_1` takes `_book_n_of`
    as its `ARG1`. Predications that do not take any other predication
    within their scope as an argument (as `_book_n_of` above does not)
    are scope representatives.

    *priority* is a function that takes a :class:`Predication` object
    and returns a rank which is used to to sort the representatives
    for each scope. As the predication alone might not contain enough
    information for useful sorting, it can be helpful to create a
    function configured for the input semantic structure *x*. If
    *priority* is `None`, representatives are sorted according to the
    following criteria:

    1. Prefer predications that are quantifiers or instances (type 'x')

    2. Prefer eventualities (type 'e') over other types

    3. Prefer tensed over untensed eventualities

    4. Finally, prefer those appearing first in *x*

    The definition of "tensed" vs "untensed" eventualities is
    grammar-specific, but it is used by several large grammars. If a
    grammar does something different, criterion (3) is ignored.
    Criterion (4) is not linguistically motivated but is used as a
    final disambiguator to ensure consistent results.

    Args:
        x: an MRS or a DMRS
        priority: a function that maps an EP to a rank for sorting
    Example:
        >>> sent = 'The new chef whose soup accidentally spilled quit.'
        >>> m = ace.parse(erg, sent).result(0).mrs()
        >>> # in this example there are 4 EPs in scope h7
        >>> _, scopes = m.scopes()
        >>> [ep.predicate for ep in scopes['h7']]
        ['_new_a_1', '_chef_n_1', '_accidental_a_1', '_spill_v_1']
        >>> # there are 2 representatives for scope h7
        >>> reps = scope.representatives(m)['h7']
        >>> [ep.predicate for ep in reps]
        ['_chef_n_1', '_spill_v_1']
    """
    _, scopes = x.scopes()
    ns_args = {src: set(arg for _, arg in roleargs)
               for src, roleargs in x.arguments(types='xeipu').items()}
    # compute descendants, but only keep ids
    descs = {id: set(d.id for d in ds)
             for id, ds in descendants(x, scopes).items()}

    reps: dict[ScopeLabel, list[Predication]] = {
        label: [] for label in scopes
    }
    for label, scope in scopes.items():
        if len(scope) == 1:
            reps[label].extend(scope)
        else:
            for predication in scope:
                others = [p.id for p in scope if p is not predication]
                args = ns_args[predication.id]
                # check if args are in the immediate scope
                if args.intersection(others):
                    continue
                # check if args are in scope descendants
                if any(args.intersection(descs[id]) for id in others):
                    continue
                # tests passed; predication is a candidate representative
                reps[label].append(predication)

    if priority is None:
        priority = _make_representative_priority(x)
    for label in reps:
        reps[label].sort(key=priority)

    return reps


_UNTENSED_VALUES = {
    '',
    'untensed',
}


def _make_representative_priority(x: ScopingSemanticStructure):
    """
    Create a function to sort scope representatives in *x*.
    """
    index = {p.id: i for i, p in enumerate(x.predications, 1)}

    def representative_priority(p: Predication) -> tuple[int, Identifier]:
        id = p.id
        type = p.type

        if x.is_quantifier(id) or type == 'x':
            rank = 0
        elif type == 'e':
            tense = x.properties(id).get('TENSE', '').lower()
            if tense in _UNTENSED_VALUES:
                rank = 2
            else:
                rank = 1
        else:
            rank = 3
        return rank, index[id]

    return representative_priority


# for backward compatibility
from delphin.sembase import ScopeRelation  # noqa
LEQ = ScopeRelation.LEQ
LHEQ = ScopeRelation.LHEQ
OUTSCOPES = ScopeRelation.OUTSCOPES
QEQ = ScopeRelation.QEQ
