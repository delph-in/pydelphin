
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


### Types

ScopeMap = Mapping[Identifier, Iterable[Identifier]]  # e.g., {'h1': ['e2', 'e6']}
ScopeConstraints = Iterable[Tuple[Identifier, str, Identifier]]

### Exceptions

class ScopeError(PyDelphinException):
    """Raised on invalid scope operations."""


### Module Functions

def tree_fragments():
    pass

def partial_ordering():
    pass

    # class ScopeTree(object):
    # """
    # An underspecified scope tree.

    # Args:
    #     top: the top scope handle
    #     scopes: mapping of scope labels to ids of scoped predications
    #     heqs: list of (hi, lo) pairs of *immediate-outscopes* constraints
    #     qeqs: list of (hi, lo) pairs of *qeq* constraints
    # Example:
    #     >>> stree = ScopeTree('h0', {'h1': [1, 2], 'h2': [3]},
    #     ...                   [('h1', 'h2')], [('h0', 'h1')])
    # """

    # __slots__ = ('top', 'tree', 'qeqs', '_nodecache', '_dcache')

    # def __init__(self, x):
    #     self.top = x.top
    #     scopes = x.scopes()
    #     heqs = x.scopal_arguments(qeq=False)
    #     qeqs = x.scopal_arguments(qeq=True)

    # def __init__(self, top, scopes, heqs=None, qeqs=None):
    #     self.top = top
    #     self.tree = {label: set() for label in scopes}
    #     self._nodecache = {label: set(ids) for label, ids in scopes.items()}
    #     self.qeqs = {}
    #     self._dcache = {}  # descendant cache

    #     if heqs:
    #         for hi, lo in heqs:
    #             if hi == lo:
    #                 raise ScopeError('scopes cannot outscope themselves')
    #             self.tree[hi].add(lo)

    #     if qeqs:
    #         for hi, lo in qeqs:
    #             self.qeqs.setdefault(hi, set()).add(lo)

    # def descendants(self, label, with_qeqs=True):
    #     """
    #     Return the set of nodes that scope lower than *label*.

    #     Args:
    #         label: the top label from which to gather descendants
    #         with_qeqs: if `True`, include descendants linked by qeq
    #     Returns:
    #         set: the set of descendants of *label*
    #     Example:
    #         >>> st = ScopeTree('h0', ['h1', 'h2', 'h3'],
    #         ...                heqs=[('h1', 'h2')], qeqs=[('h0', 'h1')])
    #         >>> st.descendants('h0')
    #         {'h1', 'h2'}
    #     """
    #     if label != self.top and label not in self.tree:
    #         raise ScopeError('invalid scope label: {}'.format(label))
    #     if label not in self._dcache:
    #         self._cache_descendants(label, with_qeqs, set())
    #     return self._dcache[label]

    # def _cache_descendants(self, label, with_qeqs, seen):
    #     if label in seen:
    #         raise ScopeError('cycle in scope tree involves: {}'
    #                          .format(', '.join(map(str, seen))))
    #     seen.add(label)

    #     children = self.tree.get(label, set())
    #     if with_qeqs:
    #         children.update(self.qeqs.get(label, []))

    #     descendants = set(children)
    #     for child in children:
    #         if child not in self._dcache:
    #             self._cache_descendants(child, with_qeqs, seen)
    #         descendants.update(self._dcache[child])

    #     self._dcache[label] = descendants

    # def outscopes(self, a, b):
    #     """
    #     Return `True` if *a* outscopes *b*.

    #     Example
    #         >>> st = ScopeTree('h0', ['h1', 'h2', 'h3'],
    #         ...                heqs=[('h1', 'h2')], qeqs=[('h0', 'h1')])
    #         >>> st.outscopes('h0', 'h2')
    #         True
    #         >>> st.outscopes('h2', 'h0')
    #         False
    #         >>> st.outscopes('h0', 'h3')
    #         False
    #     """
    #     return b in self.descendants(a)

    # def configurations(self):
    #     pass


def conjoin(labels: ScopeMap, eq_constraints: ScopeConstraints) -> ScopeMap:
    """
    Conjoin multiple scopes with equality constraints.

    Args:
        labels: an iterable of scope labels
        eq_constraints: a list of pairs of equated scope labels
    Returns:
        A mapping of the new merged scope labels to the set of old
        scope labels. Each new scope label is taken arbitrarily from
        its set of old labels.
    Example:
        >>> scope.conjoin(['h1', 'h2', 'h3'], [('h2', 'h3')])
        {'h1': {'h1'}, 'h2': {'h2', 'h3'}}
    """
    scopemap = {}
    for component in _connected_components(labels, eq_constraints):
        rep = next(iter(component))
        scopemap[rep] = component
    return scopemap


def representatives(self, nsargs: ArgumentStructure):
    """
    Find the scope representatives

    Args:
        nsargs: a mapping of non-scopal arguments from the source
            identifier (node id or intrinsic variable) to the
            target identifier (roles are not included)
    Example:
        >>> sent = 'The new chef whose soup accidentally spilled quit.'
        >>> m = ace.parse(grm, sent).result(0).mrs()
        >>> # in this example there are 4 EPs in scope h7
        >>> print('  '.join('{0.iv}:{0.predicate}'.format(ep)
        ...                 for ep in m.scopes()['h7']))
        e8:_new_a_1  x3:_chef_n_1  e15:_accidental_a_1  e16:_spill_v_1
        >>> stree = m.scopetree()
        >>> nsargs = {ep.iv: set(ep.outgoing_args('exi').values())
        ...           for ep in m.rels}
        >>> # there are 2 candidate representatives for scope h7
        >>> print(stree.representatives(nsargs)['h7'])
        ['e16', 'x3']
    """
    reps = {}
    for label in self.tree:
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


def link_subsumes(m1, m2):
    """Link-subsumes from Copestake et al. 2014.
    MRS m1 subsumes m2 if m1 is a scope-underspecified form of m2.
    That is, m2 is equivalent to m1 except it has additional label equalities."""
    pass


### Classes

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

    def scopal_arguments(self, qeq: bool = None) -> ArgumentStructure:
        """
        Return scopal arguments in the structure.

        Scopal arguments are those whose value is a range of nodes.
        """
        raise NotImplementedError()

    def non_scopal_arguments(self) -> ArgumentStructure:
        """
        Return non-scopal arguments in the structure.

        Non-scopal arguments are those whose value is a single node.
        """
        raise NotImplementedError()

    def scopes(self) -> ScopeMap:
        """
        Return a mapping of scope labels to nodes sharing the scope.
        """
        raise NotImplementedError()
