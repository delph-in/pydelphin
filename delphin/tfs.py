
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

from __future__ import unicode_literals


class FeatureStructure(object):
    """
    A feature structure.

    This class manages the access of nested features using
    dot-delimited notation (e.g., `SYNSEM.LOCAL.CAT.HEAD`).

    Args:
        featvals (dict, list): a mapping or iterable of feature paths
            to feature values
    """

    __slots__ = ['_avm', '_feats']

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
    __slots__ = ['_type', '_avm', '_feats']

    def __init__(self, type, featvals=None):
        self._type = type
        super(TypedFeatureStructure, self).__init__(featvals)

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


class TypeHierarchy(object):
    """
    A Type Hierarchy.

    Type hierarchies have certain properties, such as a unique top node,
    multiple inheritance, and unique greatest-lower-bound (glb) types.

    Note:
        Checks for unique glbs is not yet implemented.
    Args:
        top (str): unique top type
        hierarchy (dict): mapping of `{child: [parents]}`
    """
    def __init__(self, top, hierarchy=None):
        self._top = top
        self._hier = {}
        if hierarchy is None:
            self[top] = []
        elif hierarchy.get(top, False):
            raise ValueError('top type cannot have supertypes')
        else:
            hierarchy[top] = []
            loerarchy = {}  # type -> children
            for child, parents in hierarchy.items():
                for parent in parents:
                    loerarchy.setdefault(parent, []).append(child)
            agenda = [top]
            th = self._hier  # to reduce lookups in the loop
            while agenda:
                typename = agenda.pop()
                self[typename] = hierarchy[typename]
                del hierarchy[typename]
                for child in loerarchy.get(typename, []):
                    if all(parent in th for parent in hierarchy[child]):
                        agenda.append(child)
            if hierarchy:
                raise ValueError(
                    'disconnected or cyclic hierarchy; remaining: {}'
                    .format(', '.join(hierarchy)))

    def __setitem__(self, typename, parents):
        if typename in self._hier:
            raise ValueError('type already in hierarchy: ' + typename)
        ancestors = set()
        for parent in parents:
            if parent not in self._hier:
                raise ValueError('parent not in hierarchy: ' + parent)
            ancestors.update(self.ancestors(parent))
        redundant = ancestors.intersection(parents)
        if redundant:
            raise ValueError('redundant parents: {}'
                             .format(', '.join(sorted(redundant))))
        self._hier[typename] = (parents, [])
        for parent in parents:
            self._hier[parent][1].append(typename)

    # def __getitem__(self, typename):
    #     return self._hier[typename]

    def ancestors(self, typename):
        """Return the ancestor types of *typename*."""
        xs = []
        for parent in self._hier[typename][0]:
            xs.append(parent)
            xs.extend(self.ancestors(parent))
        return xs

    def descendants(self, typename):
        """Return the descendant types of *typename*."""
        xs = []
        for child in self._hier[typename][1]:
            xs.append(child)
            xs.extend(self.descendants(child))
        return xs

    def subsumes(self, a, b):
        """Return `True` if type *a* subsumes type *b*."""
        return a == b or b in self.descendants(a)

    def compatible(self, a, b):
        """Return `True` if type *a* is compatible with type *b*."""
        return len(set([a] + self.descendants(a))
                   .intersection([b] + self.descendants(b))) > 0
