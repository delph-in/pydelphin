# -*- coding: utf-8 -*-

"""
Structures and operations for quantifier scope in DELPH-IN semantics.

While the predicate-argument structure of a semantic representation is
a directed-acyclic graph, the quantifier scope is a tree overlayed on
that graph. In a fully scope-resolved structure, there is one tree
spanning the entire graph, but in underspecified representations like
MRS, there are multiple subtrees that span the graph nodes but are not
all connected together.

Each node in the scope tree (called a *scopal position*) may encompass
multiple nodes in the predicate-argument graph. Nodes that share a
scopal position are said to be in a *conjunction*.

The dependency representations EDS and DMRS develop the idea of scope
representatives (called *representative nodes* or sometimes *heads*),
whereby a single node is selected from a conjunction to represent the
conjunction as a whole.

"""

from typing import Mapping, Iterable, Tuple, Collection
from operator import itemgetter

from delphin.lnk import Lnk
from delphin import predicate
from delphin.sembase import (
    Identifier,
    ArgumentStructure,
    Predications,
    SemanticStructure
)
from delphin.exceptions import PyDelphinException
from delphin.util import _connected_components


# Constants

LEQ = 'leq'              # label equality (label-to-label)
LHEQ = 'lheq'            # label-handle equality (hole-to-label)
OUTSCOPES = 'outscopes'  # directly or indirectly takes scope over
QEQ = 'qeq'              # equality modulo quantifiers (hole-to-label)


# Types
ScopeLabel = str
ScopeRelation = str
ScopeMap = Mapping[ScopeLabel, Predications]
# Regarding literal types, see: https://www.python.org/dev/peps/pep-0563/
UnderspecifiedFragments = Mapping[ScopeLabel, 'UnderspecifiedScope']
ScopeEqualities = Iterable[Tuple[ScopeLabel, ScopeLabel]]
ScopeConstraints = Iterable[Tuple[ScopeLabel, ScopeRelation, ScopeLabel]]


# Exceptions

class ScopeError(PyDelphinException):
    """Raised on invalid scope operations."""


# Classes

class UnderspecifiedScope(tuple):
    """
    Quantifier scope with underspecified constraints.

    This class serves as the nodes in the scope tree fragments used by
    MRS (and transformations of DMRS). It combines three data
    structures:

    * the ids of predications in the immediate scope

    * a mapping of labels to :class:`UnderspecifiedScope` objects for
      scopes directly under the current scope

    * a mapping of labels to :class:`UnderspecifiedScope` objects for
      scopes qeq from the current scope

    This class is not meant to be instantiated directly, but rather is
    used in the return value of functions such as
    :func:`tree_fragments`.

    Attributes:
        ids: ids of predications in the immediate scope
        lheqs: mapping of labels to underspecified scopes directly
            under the current scope
        qeqs: mapping of labels to underspecified scopes qeq from
            the current scope
    """

    __slots__ = ()

    def __new__(cls,
                ids: Collection[Identifier],
                lheqs: UnderspecifiedFragments = None,
                qeqs: UnderspecifiedFragments = None):
        if lheqs is None:
            lheqs = {}
        if qeqs is None:
            qeqs = {}
        return super().__new__(cls, (set(ids), lheqs, qeqs))

    ids = property(
        itemgetter(0), doc='set of ids of predicates in the immediate scope')
    lheqs = property(
        itemgetter(1), doc='directly lower scopes')
    qeqs = property(
        itemgetter(2), doc='indirectly lower scopes')

    def __repr__(self):
        return 'UnderspecifiedScope({!r}, {!r}, {!r})'.format(*self, id(self))

    def __contains__(self, id):
        return (id in self.ids
                or any(id in lower for lower in self.lheqs.values())
                or any(id in lower for lower in self.qeqs.values()))


class ScopingSemanticStructure(SemanticStructure):
    """
    A semantic structure that encodes quantifier scope.

    This is a base class for semantic representations that distinguish
    scopal and non-scopal arguments, namely :class:`~delphin.mrs.MRS`
    and :class:`~delphin.dmrs.DMRS`. In addition to the attributes and
    methods of the :class:`~delphin.sembase.SemanticStructure` class,
    it also includes an :attr:`index` which indicates the non-scopal
    top of the structure. It also describes methods that allow one to
    retrieve scopal and non-scopal arguments separately, and a method
    to retrieve a mapping of scope labels to node identifiers sharing
    the labels.
    """

    __slots__ = ('index',)

    def __init__(self,
                 top: Identifier,
                 index: Identifier,
                 predications: Predications,
                 lnk: Lnk,
                 surface,
                 identifier):
        super().__init__(top, predications, lnk, surface, identifier)
        self.index = index

    def arguments(self, types=None, scopal: bool = None) -> ArgumentStructure:
        """
        Return a mapping of the argument structure.

        Args:
            types: a container of predication or variable types that
                may be targets
            scopal: if `True`, only include scopal arguments; if
                `False`, only include non-scopal arguments; if
                unspecified or `None`, include both
        """
        raise NotImplementedError()

    def scope_constraints(self) -> ScopeConstraints:
        """
        Return a list of expanded scope constraints.

        This list goes beyond the usual qeq constraints and includes
        immediate-outscopes and general outscopes constraints encoded
        in the arguments of predications.
        """
        raise NotImplementedError()

    def scopes(self) -> ScopeMap:
        """
        Return a mapping of scope labels to nodes sharing the scope.
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
    scopemap = {}
    for component in _connected_components(list(scopes), leqs):
        rep = next(iter(component))
        scopemap[rep] = []
        for label in component:
            scopemap[rep].extend(scopes[label])
    return scopemap


def tree_fragments(x: ScopingSemanticStructure,
                   prune=True) -> UnderspecifiedFragments:
    """
    Return a mapping of scope labels to underspecified tree fragments.

    Each fragment is an :class:`UnderspecifiedScope` object.

    By default the top-level mapping only includes the fragments that
    are not specified as being under another scope. By setting the
    *prune* parameter to `False` all scope labels are included in the
    mapping, which may be helpful for applications needing direct
    access to lower scopes.

    Args:
        x: an MRS or DMRS
        prune: if `True` only include top-level scopes in the mapping
    """
    scopes = x.scopes()
    fragments = {x.top: UnderspecifiedScope([])}
    for label, ps in scopes.items():
        fragments[label] = UnderspecifiedScope(ps)

    nested = set()
    for src, rel, tgt in x.scope_constraints():
        if rel == LHEQ:
            fragments[src].lheqs[tgt] = fragments[tgt]
            nested.add(tgt)
        elif rel == QEQ:
            fragments[src].qeqs[tgt] = fragments[tgt]
            nested.add(tgt)

    if prune:
        for label in nested:
            del fragments[label]

    return fragments


def representatives(x: ScopingSemanticStructure, ranker=None) -> ScopeMap:
    """
    Find the scope representatives in *x* sorted by *ranker*.

    When predications share a scope, generally one takes another as a
    non-scopal argument. For instance, the ERG analysis of a phrase
    like "very old book" has the predicates `_very_x_deg`, `_old_a_1`,
    and `_book_n_of` which all share a scope, where `_very_x_deg`
    takes `_old_a_1` as its `ARG1` and `_old_a_1` takes `_book_n_of`
    as its `ARG1`. Predications that do not take any other predication
    within their scope as an argument (as `_book_n_of` above does not)
    are scope representatives.

    The *ranker* argument is a function that takes a predication id
    and returns a rank which is used to to sort the representatives
    for each scope. As the id alone is probably not enough information
    for useful sorting, it is helpful to create a function configured
    for the input semantic structure *x*, as is done with
    :func:`make_representative_priority`. If *ranker* is not given or
    is `None`, :func:`make_representative_priority` is called on *x*
    to make a default ranker.

    Args:
        x: an MRS or a DMRS
    Example:
        >>> sent = 'The new chef whose soup accidentally spilled quit.'
        >>> m = ace.parse(erg, sent).result(0).mrs()
        >>> # in this example there are 4 EPs in scope h7
        >>> print('  '.join('{}:{}'.format(id, m[id].predicate)
        ...                 for id in m.scopes()['h7']))
        e8:_new_a_1  x3:_chef_n_1  e15:_accidental_a_1  e16:_spill_v_1
        >>> # there are 2 representatives for scope h7
        >>> scope.representatives(m)['h7']
        ['e16', 'x3']
        >>> # normalize the order with the *ranker* parameter
        >>> rp = make_representative_priority(m)
        >>> scope.representatives(m, ranker=rp)['h7']
        ['x3', 'e16']
    """
    fragments = tree_fragments(x, prune=False)
    nsargs = {src: set(roleargs.values())
              for src, roleargs in x.arguments(scopal=False).items()}

    reps = {label: [] for label in fragments}
    for label, uscope in fragments.items():
        for id in uscope.ids:
            if len(nsargs.get(id, set()).intersection(uscope.ids)) == 0:
                reps[label].append(id)

    if ranker is None:
        ranker = make_representative_priority(x)
    for label in reps:
        reps[label].sort(key=ranker)

    return reps


def make_representative_priority(x: ScopingSemanticStructure):
    """
    Create a function to sort scope representatives in *x*.

    This is the default representative ranking policy used by
    PyDelphin with the following (ordered) criteria:

    * Prefer predications that are quantifiers or are quantified

    * Prefer surface predicates over abstract predicates

    * Finally, prefer prefer those appearing first in *x*
    """
    qs = set()
    for p, q in x.quantifier_map().items():
        if q:
            qs.update((p, q))
    index = {p.id: i for i, p in enumerate(x.predications, 1)}

    def representative_priority(id: Identifier):
        if id in qs:
            rank = 0
        elif predicate.is_abstract(x[id].predicate):
            rank = 2
        else:
            rank = 1
        return rank, index[id]

    return representative_priority
