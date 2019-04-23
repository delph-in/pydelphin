
"""
Basic classes for modeling feature structures.

This module defines the :class:`FeatureStructure` and
:class:`TypedFeatureStructure` classes, which model an attribute value
matrix (AVM), with the latter including an associated type. They allow
feature access through TDL-style dot notation regular dictionary keys.

In addition, the :class:`TypeHierarchy` class implements a
multiple-inheritance hierarchy with checks for type subsumption and
compatibility.

"""

from collections.abc import Iterable

from delphin.hierarchy import (
    HierarchyNode,
    Hierarchy,
    HierarchyError)


class TypeHierarchyError(HierarchyError):
    """Raised for invalid operations on type hierarchies."""


class FeatureStructure(object):
    """
    A feature structure.

    This class manages the access of nested features using
    dot-delimited notation (e.g., `SYNSEM.LOCAL.CAT.HEAD`).

    Args:
        featvals (dict, list): a mapping or iterable of feature paths
            to feature values
    """

    __slots__ = ('_avm', '_feats')

    def __init__(self, featvals=None):
        self._avm = {}
        self._feats = []
        if isinstance(featvals, dict):
            featvals = featvals.items()
        for feat, val in list(featvals or []):
            self[feat] = val

    @classmethod
    def _default(cls): return cls(None)

    def __repr__(self):
        return '<{} object at {}>'.format(self.__class__.__name__, id(self))

    def __eq__(self, other):
        if not isinstance(other, FeatureStructure):
            return NotImplemented
        return self._avm == other._avm

    def __ne__(self, other):
        if not isinstance(other, FeatureStructure):
            return NotImplemented
        return self._avm != other._avm

    def __setitem__(self, key, val):
        avm = self._avm
        subkeys = key.split('.', 1)
        subkey = subkeys[0].upper()
        if subkey not in avm:
            self._feats.append(subkey)
        if len(subkeys) == 1:
            avm[subkey] = val
        else:
            if subkey in avm:
                subdef = avm[subkey]
            else:
                subdef = avm[subkey] = self._default()
            subdef[subkeys[1]] = val

    def __getitem__(self, key):
        subkeys = key.split('.', 1)
        subkey = subkeys[0].upper()
        val = self._avm[subkey]
        if len(subkeys) == 2:
            val = val[subkeys[1]]
        return val

    def __contains__(self, key):
        subkeys = key.split('.', 1)
        subkey = subkeys[0].upper()
        if subkey in self._avm:
            if len(subkeys) == 2:
                return subkeys[1] in self._avm[subkey]
            else:
                return True
        return False

    def get(self, key, default=None):
        """
        Return the value for *key* if it exists, otherwise *default*.
        """
        try:
            val = self[key]
        except KeyError:
            val = default
        return val

    def _is_notable(self):
        """
        Notability determines if the FeatureStructure should be listed as
        the value of a feature or if the feature should just "pass
        through" its avm to get the next value. A notable
        FeatureStructure is one with more than one sub-feature.
        """
        return self._avm is None or len(self._avm) != 1

    def features(self, expand=False):
        """
        Return the list of tuples of feature paths and feature values.

        Args:
            expand (bool): if `True`, expand all feature paths
        Example:
            >>> fs = FeatureStructure([('A.B', 1), ('A.C', 2)])
            >>> fs.features()
            [('A', <FeatureStructure object at ...>)]
            >>> fs.features(expand=True)
            [('A.B', 1), ('A.C', 2)]
        """
        fs = []
        if self._avm is not None:
            if len(self._feats) == len(self._avm):
                feats = self._feats
            else:
                feats = list(self._avm)
            for feat in feats:
                val = self._avm[feat]
                if isinstance(val, FeatureStructure):
                    if not expand and val._is_notable():
                        fs.append((feat, val))
                    else:
                        for subfeat, subval in val.features(expand=expand):
                            fs.append(('{}.{}'.format(feat, subfeat), subval))
                else:
                    fs.append((feat, val))
        return fs


class TypedFeatureStructure(FeatureStructure):
    """
    A typed :class:`FeatureStructure`.

    Args:
        type (str): type name
        featvals (dict, list): a mapping or iterable of feature paths
            to feature values
    """
    __slots__ = '_type'

    def __init__(self, type, featvals=None):
        self._type = type
        super().__init__(featvals)

    def __repr__(self):
        return '<TypedFeatureStructure object ({}) at {}>'.format(
            self.type, id(self)
        )

    def __eq__(self, other):
        if not isinstance(other, TypedFeatureStructure):
            return NotImplemented
        return self._type == other._type and self._avm == other._avm

    def __ne__(self, other):
        if not isinstance(other, TypedFeatureStructure):
            return NotImplemented
        return self._type != other._type or self._avm != other._avm

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value


class TypeHierarchyNode(HierarchyNode):
    """
    A node in a TypeHierarchy.

    When the node is inserted into a :class:`TypeHierarchy` and other
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


class TypeHierarchy(Hierarchy):
    """
    A Type Hierarchy.

    Type hierarchies have certain properties, such as a unique top
    node, multiple inheritance, case insensitivity, and unique
    greatest-lower-bound (glb) types.

    Note:
        Checks for unique glbs is not yet implemented.

    TypeHierarchies may be constructed when instantiating the class or
    via the :meth:`update` method using a dictionary mapping type
    names to node values, or one-by-one using dictionary-like access.
    In both cases, the node values may be an individual parent name,
    an iterable of parent names, or a :class:`TypeHierarchyNode`
    object. Retrieving a node via dictionary access on the typename
    returns a :class:`TypeHierarchyNode` regardless of the method used
    to create the node.

    >>> th = TypeHierarchy('*top*', {'can-fly': '*top*'})
    >>> th.update({'can-swim': '*top*', 'can-walk': '*top*'})
    >>> th['butterfly'] = ('can-fly', 'can-walk')
    >>> th['duck'] = TypeHierarchyNode(
    ...     ('can-fly', 'can-swim', 'can-walk'),
    ...     data='some info relating to ducks...')
    >>> th['butterfly'].data = 'some info relating to butterflies'

    In some ways the TypeHierarchy behaves like a dictionary, but it
    is not a subclass of :py:class:`dict` and does not implement all
    its methods. Also note that some methods ignore the top node,
    which make certain actions easier:

    >>> th = TypeHierarchy('*top*', {'a': '*top*', 'b': 'a', 'c': 'a'})
    >>> len(th)
    3
    >>> list(th)
    ['a', 'b', 'c']
    >>> TypeHierarchy('*top*', dict(th.items())) == th
    True

    But others do not ignore the top node, namely those where you can
    request it specifically:

    >>> '*top*' in th
    True
    >>> th['*top*']
    <TypeHierarchyNode ... >

    Args:
        top (str): unique top type
        hierarchy (dict): mapping of `{child: node}` (see description
            above concerning the `node` values)
    Attributes:
        top: the hierarchy's top type
    """

    _nodecls = TypeHierarchyNode
    _errcls  = TypeHierarchyError

    def _update_children(self, typename, node):
        for parent in node.parents:
            self._hier[parent]._children.add(typename)

    def _check_node_integrity(self, node):
        ancestors = set()
        for parent in node.parents:
            if parent not in self._hier:
                raise TypeHierarchyError('parent not in hierarchy: ' + parent)
            ancestors.update(self.ancestors(parent))
        redundant = ancestors.intersection(node.parents)
        if redundant:
            raise TypeHierarchyError('redundant parents: {}'
                                     .format(', '.join(sorted(redundant))))

    def _node_is_eligible(self, node):
        hierarchy = self._hier
        return all(parent in hierarchy for parent in node.parents)

    def _ensure_node(self, typename, node):
        if isinstance(node, str):
            node = TypeHierarchyNode([node])
        elif isinstance(node, Iterable):
            node = TypeHierarchyNode(node)
        elif not isinstance(node, TypeHierarchyNode):
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
        a, b = a.lower(), b.lower()
        return a == b or b in self.descendants(a)

    def compatible(self, a, b):
        """Return `True` if type *a* is compatible with type *b*."""
        a, b = a.lower(), b.lower()
        return len(set([a] + self.descendants(a))
                   .intersection([b] + self.descendants(b))) > 0
