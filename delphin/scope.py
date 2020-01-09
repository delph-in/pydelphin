# -*- coding: utf-8 -*-

"""
Structures and operations for quantifier scope in DELPH-IN semantics.
"""

from typing import (Optional, Mapping, Iterable, List, Tuple, Dict)

from delphin.lnk import Lnk
from delphin.sembase import (
    Identifier,
    Role,
    Predication,
    Predications,
    SemanticStructure
)
from delphin.exceptions import PyDelphinException
from delphin.util import _connected_components
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


# Constants

LEQ = 'leq'              # label equality (label-to-label)
LHEQ = 'lheq'            # label-handle equality (hole-to-label)
OUTSCOPES = 'outscopes'  # directly or indirectly takes scope over
QEQ = 'qeq'              # equality modulo quantifiers (hole-to-label)


# Types
ScopeLabel = str
ScopeRelation = str
ScopeMap = Mapping[ScopeLabel, Predications]
DescendantMap = Mapping[Identifier, List[Predication]]
ScopalRoleArgument = Tuple[Role, ScopeRelation, Identifier]
ScopalArgumentStructure = Mapping[Identifier, List[ScopalRoleArgument]]
# Regarding literal types, see: https://www.python.org/dev/peps/pep-0563/
ScopeEqualities = Iterable[Tuple[ScopeLabel, ScopeLabel]]


# Exceptions

class ScopeError(PyDelphinException):
    """Raised on invalid scope operations."""


# Classes

class ScopingSemanticStructure(SemanticStructure):
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

    def __init__(self,
                 top: Optional[Identifier],
                 index: Optional[Identifier],
                 predications: Predications,
                 lnk: Optional[Lnk],
                 surface,
                 identifier):
        super().__init__(top, predications, lnk, surface, identifier)
        self.index = index

    def scopal_arguments(self, scopes=None) -> ScopalArgumentStructure:
        """
        Return a mapping of the scopal argument structure.

        Unlike :meth:`SemanticStructure.arguments`, the list of
        arguments is a 3-tuple including the scopal relation: (role,
        scope_relation, scope_label).

        Args:
            scopes: mapping of scope labels to lists of predications
        """
        raise NotImplementedError()

    def scopes(self) -> Tuple[ScopeLabel, ScopeMap]:
        """
        Return a tuple containing the top label and the scope map.

        The top label is the label of the top scope in the scope map.

        The scope map is a dictionary mapping scope labels to the
        lists of predications sharing a scope.
        """
        raise NotImplementedError()


# Module Functions

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
    scopemap: Dict[ScopeLabel, List[Predication]] = {}
    for component in _connected_components(list(scopes), leqs):
        chosen_label = next(iter(component))
        scopemap[chosen_label] = []
        for label in component:
            scopemap[chosen_label].extend(scopes[label])
    return scopemap


def descendants(x: ScopingSemanticStructure,
                scopes: ScopeMap = None) -> DescendantMap:
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
    descs: Dict[Identifier, List[Predication]] = {}
    for p in x.predications:
        _descendants(descs, p.id, scargs, scopes)
    return descs


def _descendants(descs: Dict[Identifier, List[Predication]],
                 id: Identifier,
                 scargs: ScopalArgumentStructure,
                 scopes: ScopeMap) -> None:
    if id in descs:
        return
    descs[id] = []
    for role, relation, label in scargs[id]:
        assert isinstance(label, str)
        for p in scopes.get(label, []):
            descs[id].append(p)
            _descendants(descs, p.id, scargs, scopes)
            descs[id].extend(descs[p.id])


def representatives(x: ScopingSemanticStructure, priority=None) -> ScopeMap:
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

    4. Finally, prefer prefer those appearing first in *x*

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

    reps: Dict[ScopeLabel, List[Predication]] = {
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

    def representative_priority(p: Predication):
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
