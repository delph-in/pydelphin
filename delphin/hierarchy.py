
"""
Basic support for hierarchies.

The :class:`Hierarchy` and :class:`HierarchyNode` classes implement a
single-parented hierarchy, i.e., a tree. While it can be used as-is,
it mainly serves as a base class for other hierarchies, such as
:class:`delphin.tfs.TypeHierarchy`, which extends it to allow for
multiple parents, case-insensitive identifiers, subsumption tests,
etc.
"""

from collections.abc import Iterable

from delphin.exceptions import PyDelphinException


class HierarchyError(PyDelphinException):
    """Raised for invalid operations on hierarchies."""


def _norm_id(id):
    return id


class HierarchyNode(object):
    """
    A node in a Hierarchy.

    When the node is inserted into a :class:`Hierarchy` and other
    nodes are inserted which specify this node as its parent, the
    :attr:`children` attribute will be updated to reflect those
    subtypes. The :attr:`children` list is not meant to be set
    manually.

    Args:
        parent: the node's parent
        data: arbitrary data associated with the node
    Attributes:
        parent: the parent of the node
        children: the children of the node
        data: data associated with the node, or `None`
    """

    __slots__ = ('_parent', '_children', 'data')

    def __init__(self, parent, data=None):
        self._parent = parent
        self._children = set()
        self.data = data

    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        return list(self._children)

    def __eq__(self, other):
        if not isinstance(other, HierarchyNode):
            return NotImplemented
        return (self.parent == other.parent
                and self.children == other.children
                and self.data == other.data)

    def __ne__(self, other):
        if not isinstance(other, HierarchyNode):
            return NotImplemented
        return not (self == other)


class Hierarchy(object):
    """
    A Hierarchy.

    Hierarchies may be constructed when instantiating the class or
    via the :meth:`update` method using a dictionary mapping identifiers
    to node values, or one-by-one using dictionary-like access.
    In both cases, the node values may be an individual parent name,
    an iterable of parent names, or a :class:`HierarchyNode`
    object. Retrieving a node via dictionary access on the identifier
    returns a :class:`HierarchyNode` regardless of the method used
    to create the node.

    >>> h = Hierarchy('*top*', {'food': '*top*'})
    >>> th.update({'utensil': '*top*', 'fruit': 'food'})
    >>> th['apple'] = 'fruit'
    >>> th['knife'] = HierarchyNode('utensil', data='info about knives')
    >>> th['apple'].data = 'info about apples'

    In some ways the Hierarchy behaves like a dictionary, but it
    is not a subclass of :py:class:`dict` and does not implement all
    its methods. Also note that some methods ignore the top node,
    which make certain actions easier:

    >>> h = Hierarchy('*top*', {'a': '*top*', 'b': 'a', 'c': 'a'})
    >>> len(h)
    3
    >>> list(h)
    ['a', 'b', 'c']
    >>> Hierarchy('*top*', dict(h.items())) == h
    True

    But others do not ignore the top node, namely those where you can
    request it specifically:

    >>> '*top*' in h
    True
    >>> h['*top*']
    <HierarchyNode ... >

    Args:
        top (str): unique top identifier
        hierarchy (dict): mapping of `{identifier: node}` (see
            description above concerning the `node` values)
    Attributes:
        top: the hierarchy's top identifier
    """

    # _nodecls = HierarchyNode
    _nodecls = HierarchyNode
    _errcls = HierarchyError

    def __init__(self, top, hierarchy=None, normalize_identifier=None):
        if not normalize_identifier:
            self._norm = _norm_id
        elif not callable(normalize_identifier):
            raise TypeError('not callable: {!r}'.format(normalize_identifier))
        else:
            self._norm = normalize_identifier
        top = self._norm(top)
        self._top = top
        self._hier = {top: self._nodecls(None)}
        if hierarchy is not None:
            self.update(hierarchy)

    @property
    def top(self):
        return self._top

    def __eq__(self, other):
        if not isinstance(other, Hierarchy):
            return NotImplemented
        return self._top == other._top and self._hier == other._hier

    def __ne__(self, other):
        if not isinstance(other, Hierarchy):
            return NotImplemented
        return not self.__eq__(other)

    def __setitem__(self, identifier, node):
        node = self._ensure_node(identifier, node)
        self._insert(identifier, node)

    def _ensure_node(self, identifier, node):
        if isinstance(node, str):
            node = HierarchyNode(node)
        elif not isinstance(node, HierarchyNode):
            raise TypeError("cannot set '{}' to object of type {}"
                            .format(identifier, node.__class__.__name__))
        return node

    def _insert(self, identifier, node):
        identifier = self._norm(identifier)
        if identifier in self._hier:
            raise self._errcls('already in hierarchy: ' + identifier)
        self._check_node_integrity(node)
        self._hier[identifier] = node
        self._update_children(identifier, node)

    def _update_children(self, identifier, node):
        self._hier[node.parent]._children.add(identifier)

    def _check_node_integrity(self, node):
        if node.parent not in self._hier:
            raise self._errcls('parent not in hierarchy: ' + str(node.parent))

    def __getitem__(self, identifier):
        return self._hier[self._norm(identifier)]

    def __iter__(self):
        return iter(identifier for identifier in self._hier
                    if identifier != self._top)

    def __contains__(self, identifier):
        return self._norm(identifier) in self._hier

    def __len__(self):
        return len(self._hier) - 1  # ignore top

    def items(self):
        """
        Return the (identifier, node) pairs excluding the top node.
        """
        hier = self._hier
        return [(identifier, hier[identifier]) for identifier in self]

    def update(self, subhierarchy):
        """
        Incorporate *subhierarchy* into the hierarchy.

        This is nearly the same as the following:

        >>> for identifier, node in subhierarchy.items():
        ...     hierarchy[identifier] = node
        ...

        However the `update()` method ensures that the nodes are
        inserted in an order that does not result in an intermediate
        state being disconnected or cyclic, and raises an error if
        it cannot avoid such a state due to *subhierarchy* being
        invalid when inserted into the main hierarchy.

        Args:
            subhierarchy (dict): hierarchy to incorporate
        Raises:
            HierarchyError: when inserting *subhierarchy* leads to
                a disconnected or cyclic hierarchy.
        """
        hierarchy = self._hier
        subhier = {self._norm(t): self._ensure_node(t, n)
                   for t, n in subhierarchy.items()}
        while subhier:
            eligible = [identifier for identifier, node in subhier.items()
                        if self._node_is_eligible(node)]
            if not eligible:
                raise self._errcls(
                    'disconnected or cyclic hierarchy; remaining: {}'
                    .format(', '.join(subhier)))
            for identifier in eligible:
                self._insert(identifier, subhier[identifier])
                del subhier[identifier]

    def _node_is_eligible(self, node):
        return node.parent in self._hier

    def ancestors(self, identifier):
        """Return the ancestor node identifiers of *identifier*."""
        parent = self._hier[identifier].parent
        if parent is not None:
            xs = [parent] + self.ancestors(parent)
        else:
            xs = []
        return xs

    def descendants(self, identifier):
        """Return the descendant node identifiers of *identifier*."""
        xs = []
        for child in self._hier[identifier].children:
            xs.append(child)
            xs.extend(self.descendants(child))
        return xs


class MultiHierarchyNode(HierarchyNode):
    """
    A node in a MultiHierarchy.

    When the node is inserted into a :class:`MultiHierarchy` and other
    nodes are inserted which specify this node as its parent, the
    :attr:`children` attribute will be updated to reflect those
    subtypes. The :attr:`children` list is not meant to be set
    manually.

    Args:
        parents: an iterable of the type's parents
        data: arbitrary data associated with the type
    Attributes:
        parents: the parents of the type (immediate supertypes)
        children: the children of the type (immediate subtypes)
        data: data associated with the type, or `None`
    """

    def __init__(self, parents, data=None):
        if parents is None:  # top node, probably
            parent = parents
        elif not parents:  # empty iterable, probably
            raise ValueError('no parents specified')
        else:
            parent = tuple(map(self.normalize_identifier, parents))
        super().__init__(parent, data=data)

    @staticmethod
    def normalize_identifier(typename):
        return typename.lower()

    @property
    def parents(self):
        if self._parent is None:
            return []
        else:
            return list(self._parent)


class MultiHierarchy(Hierarchy):
    """
    A Multiply-Inheriting Hierarchy.

    Args:
        top (str): unique top type
        hierarchy (dict): mapping of `{child: node}` (see description
            above concerning the `node` values)
    Attributes:
        top: the hierarchy's top type
    """

    _nodecls = MultiHierarchyNode

    def _update_children(self, typename, node):
        for parent in node.parents:
            self._hier[parent]._children.add(typename)

    def _check_node_integrity(self, node):
        ancestors = set()
        for parent in node.parents:
            if parent not in self._hier:
                raise self._errcls('parent not in hierarchy: ' + parent)
            ancestors.update(self.ancestors(parent))
        redundant = ancestors.intersection(node.parents)
        if redundant:
            raise self._errcls('redundant parents: {}'
                               .format(', '.join(sorted(redundant))))

    def _node_is_eligible(self, node):
        hierarchy = self._hier
        return all(parent in hierarchy for parent in node.parents)

    def _ensure_node(self, typename, node):
        if isinstance(node, str):
            node = MultiHierarchyNode([node])
        elif isinstance(node, Iterable):
            node = MultiHierarchyNode(node)
        elif not isinstance(node, MultiHierarchyNode):
            raise TypeError("cannot set '{}' to object of type {}"
                            .format(typename, node.__class__.__name__))
        return node

    def ancestors(self, typename):
        """Return the ancestor types of *typename*."""
        xs = []
        for parent in self._hier[typename].parents:
            xs.append(parent)
            xs.extend(self.ancestors(parent))
        return xs

    def subsumes(self, a, b):
        """Return `True` if type *a* subsumes type *b*."""
        norm = self._norm
        a, b = norm(a), norm(b)
        return a == b or b in self.descendants(a)

    def compatible(self, a, b):
        """Return `True` if type *a* is compatible with type *b*."""
        a, b = a.lower(), b.lower()
        return len(set([a] + self.descendants(a))
                   .intersection([b] + self.descendants(b))) > 0
