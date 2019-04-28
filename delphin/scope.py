
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

from typing import Mapping, Iterable, Tuple

from delphin.lnk import Lnk
from delphin.sembase import (
    Identifier,
    ArgumentStructure,
    Predications,
    SemanticStructure
)
from delphin.exceptions import PyDelphinException
from delphin.util import _connected_components


# Constants

LHEQ = 'lheq'            # label-handle equality
OUTSCOPES = 'outscopes'  # directly or indirectly takes scope over
QEQ = 'qeq'              # equality modulo quantifiers


# Types

ScopeMap = Mapping[Identifier, Predications]
ScopeEqualities = Iterable[Tuple[str, str]]
ScopeConstraints = Iterable[Tuple[str, str, str]]


# Exceptions

class ScopeError(PyDelphinException):
    """Raised on invalid scope operations."""


# Classes

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


def domains(x: ScopingSemanticStructure) -> ScopeMap:
    """
    Return a mapping of scope labels to their domains.

    The domain of a scope is the set of predications in the immediate
    scope plus those in lower scopes as determined by the
    predications' scopal arguments.

    Args:
        scopes: a mapping of scope labels to predications
        constraints: a list of (handle, relation, label) scope
            constraint triples
    Returns:
        A mapping of scope labels to their domains.
    """
    scopemap = {}
    consmap = {}
    for src, rel, tgt in constraints:
        if rel != OUTSCOPES:
            consmap.setdefault(src, []).append(tgt)
    for label in scopes:
        _update_domain(scopemap, label, scopes, consmap)
    return scopemap


def _update_domain(scopemap, label, scopes, consmap):
    if label not in scopemap:
        entities = scopes.get(label, [])
        for label2 in consmap.get(label, []):
            entities.extend(_update_domain(scopemap, label2, scopes, consmap))
        scopemap[label] = entities
    return scopemap[label]


def representatives(x: ScopingSemanticStructure) -> ScopeMap:
    """
    Find the scope representatives

    Args:
        x: an MRS or a DMRS
    Example:
        >>> sent = 'The new chef whose soup accidentally spilled quit.'
        >>> m = ace.parse(erg, sent).result(0).mrs()
        >>> # in this example there are 4 EPs in scope h7
        >>> print('  '.join('{0.iv}:{0.predicate}'.format(ep)
        ...                 for ep in m.scopes()['h7']))
        e8:_new_a_1  x3:_chef_n_1  e15:_accidental_a_1  e16:_spill_v_1
        >>> reps = scope.representatives(m)
        >>> # there are 2 candidate representatives for scope h7
        >>> print([ep.iv for ep in reps['h7']])
        ['x3', 'e16']
    """
    fullscopes = domains(x)
    reps = {}
    for label,  in fullscopes:
        ids = self._nodecache[label]
        scoped_ids = set(ids)
        for desc_label in self.descendants(label):
            scoped_ids.update(self._nodecache[desc_label])
        nested_scopes = {id: scoped_ids.intersection(nsargs.get(id))
                         for id in ids}
        def rep_test(id):
            return len(scoped_ids.intersection(nsargs.get(id))) == 0

        candidates = list(filter(rep_test, ids))
        reps[label] = candidates
    return reps
