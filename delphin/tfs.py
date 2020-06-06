
"""
Basic classes for modeling feature structures.
"""

from delphin.hierarchy import MultiHierarchy
from delphin.exceptions import PyDelphinException
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


class TFSError(PyDelphinException):
    """Raised on invalid feature structure operations."""


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
    def _default(cls):
        return cls(None)

    def __repr__(self):
        return '<{} object at {}>'.format(self.__class__.__name__, id(self))

    def __eq__(self, other):
        if not isinstance(other, FeatureStructure):
            return NotImplemented
        return self._avm == other._avm

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
                if not hasattr(subdef, '__setitem__'):
                    raise TFSError(
                        f'{type(subdef)!r} object at feature '
                        f'{subkey} does not support item assignment')
            else:
                subdef = avm[subkey] = self._default()
            subdef[subkeys[1]] = val

    def __getitem__(self, key):
        first, _, remainder = key.partition('.')
        val = self._avm[first.upper()]
        if remainder:
            val = val[remainder]
        return val

    def __delitem__(self, key):
        first, _, remainder = key.partition('.')
        if remainder:
            fs = self._avm[first.upper()]
            del fs[remainder]
        else:
            del self._avm[first.upper()]

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

    @property
    def type(self):
        """The type assigned to the feature structure."""
        return self._type

    @type.setter
    def type(self, value):
        self._type = value


class TypeHierarchy(MultiHierarchy):
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

    def __init__(self, top, hierarchy=None, data=None,
                 normalize_identifier=None):
        if not normalize_identifier:
            normalize_identifier = str.lower
        super().__init__(top,
                         hierarchy=hierarchy,
                         data=data,
                         normalize_identifier=normalize_identifier)
