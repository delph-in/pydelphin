
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

from delphin.exceptions import PyDelphinException
from delphin.util import _connected_components


class ScopeError(PyDelphinException):
    """Raised on invalid scope operations."""


class ScopeTree(object):
    """
    An underspecified scope tree.

    Args:
        top: the top scope handle
        labels: list of scope labels
        heqs: list of (hi, lo) pairs of *immediate-outscopes* constraints
        qeqs: list of (hi, lo) pairs of *qeq* constraints
    """

    __slots__ = ('top', 'tree', 'qeqs', '_dcache')

    def __init__(self, top, labels, heqs=None, qeqs=None):
        self.top = top
        self.tree = {label: set() for label in labels}
        self.qeqs = {}
        self._dcache = {}

        if heqs:
            for hi, lo in heqs:
                if hi == lo:
                    raise ScopeError('scopes cannot outscope themselves')
                self.tree[hi].add(lo)

        if qeqs:
            for hi, lo in qeqs:
                self.qeqs.setdefault(hi, set()).add(lo)

    def descendants(self, label, with_qeqs=True):
        """
        Return the set of nodes that scope lower than *label*.

        Args:
            label: the top label from which to gather descendants
            with_qeqs: if `True`, include descendants linked by qeq
        Returns:
            set: the set of descendants of *label*
        Example:
            >>> st = ScopeTree('h0', ['h1', 'h2', 'h3'],
            ...                heqs=[('h1', 'h2')], qeqs=[('h0', 'h1')])
            >>> st.descendants('h0')
            {'h1', 'h2'}
        """
        if label != self.top and label not in self.tree:
            raise ScopeError('invalid scope label: {}'.format(label))
        if label not in self._dcache:
            self._cache_descendants(label, with_qeqs, set())
        return self._dcache[label]

    def _cache_descendants(self, label, with_qeqs, seen):
        if label in seen:
            raise ScopeError('cycle in scope tree involves: {}'
                             .format(', '.join(map(str, seen))))
        seen.add(label)

        children = self.tree.get(label, set())
        if with_qeqs:
            children.update(self.qeqs.get(label, []))

        descendants = set(children)
        for child in children:
            if child not in self._dcache:
                self._cache_descendants(child, with_qeqs, seen)
            descendants.update(self._dcache[child])

        self._dcache[label] = descendants

    def outscopes(self, a, b):
        """
        Return `True` if *a* outscopes *b*.

        Example
            >>> st = ScopeTree('h0', ['h1', 'h2', 'h3'],
            ...                heqs=[('h1', 'h2')], qeqs=[('h0', 'h1')])
            >>> st.outscopes('h0', 'h2')
            True
            >>> st.outscopes('h2', 'h0')
            False
            >>> st.outscopes('h0', 'h3')
            False
        """
        return b in self.descendants(a)

    def configurations(self):
        pass


def conjoin(scopes, eq_constraints):
    """
    Conjoin multiple scopes with equality constraints.

    Args:
        scopes: an iterable of scope labels
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
    for component in _connected_components(scopes, eq_constraints):
        rep = next(iter(component))
        scopemap[rep] = component
    return scopemap
