
"""
Basic support for hierarchies.
"""

from delphin.exceptions import PyDelphinException
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


class HierarchyError(PyDelphinException):
    """Raised for invalid operations on hierarchies."""


def _norm_id(id):
    """Default id normalizer does nothing."""
    return id


class MultiHierarchy(object):
    """
    A Multiply-inheriting Hierarchy.

    Hierarchies may be constructed when instantiating the class or via
    the :meth:`update` method using a dictionary mapping identifiers
    to parents. In both cases, the parents may be a string of
    whitespace-separated parent identifiers or a tuple of (possibly
    non-string) identifiers. Also, both methods may take a `data`
    parameter which accepts a mapping from identifiers to arbitrary
    data. Data for identifiers may be get and set individually with
    dictionary key-access.

    >>> h = MultiHierarchy('*top*', {'food': '*top*',
    ...                              'utensil': '*top*'})
    >>> th.update({'fruit': 'food', 'apple': 'fruit'})
    >>> th['apple'] = 'info about apples'
    >>> th.update({'knife': 'utensil'},
    ...           data={'knife': 'info about knives'})
    >>> th.update({'vegetable': 'food', 'tomato': 'fruit vegetable'})

    In some ways the MultiHierarchy behaves like a dictionary, but it
    is not a subclass of :py:class:`dict` and does not implement all
    its methods. Also note that some methods ignore the top node,
    which make certain actions easier:

    >>> h = Hierarchy('*top*', {'a': '*top*', 'b': 'a', 'c': 'a'})
    >>> len(h)
    3
    >>> list(h)
    ['a', 'b', 'c']
    >>> Hierarchy('*top*', {id: h.parents(id) for id in h}) == h
    True

    But others do not ignore the top node, namely those where you can
    request it specifically:

    >>> '*top*' in h
    True
    >>> print(h['*top*'])
    None
    >>> h.children('*top*')
    {'a'}

    Args:
        top: the unique top identifier
        hierarchy: a mapping of node identifiers to parents (see
            description above concerning the possible parent values)
        data: a mapping of node identifiers to arbitrary data
        normalize_identifier: a unary function used to normalize
            identifiers (e.g., case normalization)
    Attributes:
        top: the hierarchy's top node identifier
    """

    def __init__(self, top, hierarchy=None, data=None,
                 normalize_identifier=None):
        if not normalize_identifier:
            self._norm = _norm_id
        elif not callable(normalize_identifier):
            raise TypeError(f'not callable: {normalize_identifier!r}')
        else:
            self._norm = normalize_identifier
        top = self._norm(top)
        self._top = top
        self._hier = {top: ()}
        self._loer = {top: set()}
        self._data = {}
        if hierarchy is not None:
            self.update(hierarchy, data)

    @property
    def top(self):
        return self._top

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self._top == other._top
                and self._hier == other._hier
                and self._data == other._data)

    def __getitem__(self, identifier):
        identifier = self._norm(identifier)
        data = None
        try:
            data = self._data[identifier]
        except KeyError:
            if identifier not in self:
                raise
        return data

    def __setitem__(self, identifier, data):
        identifier = self._norm(identifier)
        if identifier not in self:
            raise HierarchyError(
                f'cannot set data; not in hierarchy: {identifier}')
        self._data[identifier] = data

    def __iter__(self):
        return iter(identifier for identifier in self._hier
                    if identifier != self._top)

    def __contains__(self, identifier):
        return self._norm(identifier) in self._hier

    def __len__(self):
        return len(self._hier) - 1  # ignore top

    def items(self):
        """
        Return the (identifier, data) pairs excluding the top node.
        """
        value = self.__getitem__
        return [(identifier, value(identifier)) for identifier in self]

    def update(self, subhierarchy=None, data=None):
        """
        Incorporate *subhierarchy* and *data* into the hierarchy.

        This method ensures that nodes are inserted in an order that
        does not result in an intermediate state being disconnected or
        cyclic, and raises an error if it cannot avoid such a state
        due to *subhierarchy* being invalid when inserted into the
        main hierarchy. Updates are atomic, so *subhierarchy* and
        *data* will not be partially applied if there is an error in
        the middle of the operation.

        Args:
            subhierarchy: mapping of node identifiers to parents
            data: mapping of node identifiers to data objects
        Raises:
            HierarchyError: when *subhierarchy* or *data* cannot be
                incorporated into the hierarchy
        Examples:
            >>> h = MultiHierarchy('*top*')
            >>> h.update({'a': '*top*'})
            >>> h.update({'b': '*top*'}, data={'b': 5})
            >>> h.update(data={'a': 3})
            >>> h['b'] - h['a']
            2
        """
        subhierarchy, data = self.validate_update(subhierarchy, data)

        # modify these locally in case of errors
        hier = dict(self._hier)
        loer = dict(self._loer)

        while subhierarchy:
            eligible = _get_eligible(hier, subhierarchy)

            for identifier in eligible:
                parents = subhierarchy.pop(identifier)
                _validate_parentage(identifier, parents, hier)
                hier[identifier] = parents
                loer[identifier] = set()
                for parent in parents:
                    loer[parent].add(identifier)

        # assign to self if all tests have passed
        self._hier = hier
        self._loer = loer
        self._data.update(data)

    def parents(self, identifier):
        """Return the immediate parents of *identifier*."""
        identifier = self._norm(identifier)
        return self._hier[identifier]

    def children(self, identifier):
        """Return the immediate children of *identifier*."""
        identifier = self._norm(identifier)
        return self._loer[identifier]

    def ancestors(self, identifier):
        """Return the ancestors of *identifier*."""
        identifier = self._norm(identifier)
        return _ancestors(identifier, self._hier)

    def descendants(self, identifier):
        """Return the descendants of *identifier*."""
        identifier = self._norm(identifier)
        xs = set()
        for child in self._loer[identifier]:
            xs.add(child)
            xs.update(self.descendants(child))
        return xs

    def subsumes(self, a, b):
        """
        Return `True` if node *a* subsumes node *b*.

        A node is subsumed by the other if it is a descendant of the
        other node or if it is the other node. It is not a commutative
        operation, so `subsumes(a, b) != subsumes(b, a)`, except for
        the case where `a == b`.

        Args:
            a: a node identifier
            b: a node identifier
        Examples:
            >>> h = MultiHierarchy('*top*', {'a': '*top*',
            ...                              'b': '*top*',
            ...                              'c': 'b'})
            >>> all(h.subsumes(h.top, x) for x in h)
            True
            >>> h.subsumes('a', h.top)
            False
            >>> h.subsumes('a', 'b')
            False
            >>> h.subsumes('b', 'c')
            True
        """
        norm = self._norm
        a, b = norm(a), norm(b)
        return a == b or b in self.descendants(a)

    def compatible(self, a, b):
        """
        Return `True` if node *a* is compatible with node *b*.

        In a multiply-inheriting hierarchy, node compatibility means
        that two nodes share a common descendant. It is a commutative
        operation, so `compatible(a, b) == compatible(b, a)`. Note
        that in a singly-inheriting hierarchy, two nodes are never
        compatible by this metric.

        Args:
            a: a node identifier
            b: a node identifier
        Examples:
            >>> h = MultiHierarchy('*top*', {'a': '*top*',
            ...                              'b': '*top*'})
            >>> h.compatible('a', 'b')
            False
            >>> h.update({'c': 'a b'})
            >>> h.compatible('a', 'b')
            True
        """
        norm = self._norm
        a, b = norm(a), norm(b)
        a_lineage = self.descendants(a).union([a])
        b_lineage = self.descendants(b).union([b])
        return len(a_lineage.intersection(b_lineage)) > 0

    def validate_update(self, subhierarchy, data):
        """
        Check if the update can apply to the current hierarchy.

        This method returns (*subhierarchy*, *data*) with normalized
        identifiers if the update is valid, otherwise it will raise a
        :exc:`HierarchyError`.

        Raises:
            HierarchyError: when the update is invalid
        """
        subhierarchy, data = _normalize_update(self._norm, subhierarchy, data)
        ids = set(self._hier).intersection(subhierarchy)
        if ids:
            raise HierarchyError(
                'already in hierarchy: {}'.format(', '.join(ids)))

        ids = set(data).difference(set(self._hier).union(subhierarchy))
        if ids:
            raise HierarchyError(
                'cannot update data; not in hierarchy: {}'
                .format(', '.join(ids)))
        return subhierarchy, data


def _ancestors(id, hier):
    xs = set()
    for parent in hier[id]:
        xs.add(parent)
        xs.update(_ancestors(parent, hier))
    return xs


def _normalize_update(norm, subhierarchy, data):
    sub = {}
    if subhierarchy:
        for id, parents in subhierarchy.items():
            if isinstance(parents, str):
                parents = parents.split()
            id = norm(id)
            parents = tuple(map(norm, parents))
            sub[id] = parents
    dat = {}
    if data:
        dat = {norm(id): obj for id, obj in data.items()}
    return sub, dat


def _get_eligible(hier, sub):
    eligible = [id for id, parents in sub.items()
                if all(parent in hier for parent in parents)]
    if not eligible:
        raise HierarchyError(
            'disconnected or cyclic hierarchy; remaining: {}'
            .format(', '.join(sub)))
    return eligible


def _validate_parentage(id, parents, hier):
    ancestors = set()
    for parent in parents:
        ancestors.update(_ancestors(parent, hier))
    redundant = ancestors.intersection(parents)
    if redundant:
        raise HierarchyError(
            '{} has redundant parents: {}'
            .format(id, ', '.join(sorted(redundant))))


# single-parented hierarchy might be something like this:
# class Hierarchy(MultiHierarchy):
#     def parent(self, identifier):
#         identifier = self._norm(identifier)
#         parents = self._hier[identifier]
#         if parents:
#             parents = parents[0]
#         return parents

#     def validate_update(self, subhierarchy, data):
#         """
#         Check if the update can apply to the current hierarchy.

#         Raises:
#             HierarchyError: when the update is invalid
#         """
#         subhierarchy, data = super().validate_update(subhierarchy, data)
#         for id, parents in subhierarchy.items():
#             if len(parents) != 1:
#                 raise HierarchyError(
#                     '{} has more than one parent: {}'
#                     .format(id, ', '.join(parents)))
#         return subhierarchy, data
