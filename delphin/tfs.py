
from __future__ import unicode_literals

"""
Basic classes for modeling feature structures.

This module defines the :class:`FeatureStructure` and
:class:`TypedFeatureStructure` classes, which model an attribute value
matrix (AVM), with the latter including an associated type. They allow
feature access through TDL-style dot notation regular dictionary keys.

"""


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

    def features(self):
        """
        Return the list of tuples of feature paths and feature values.
        """
        fs = []
        if self._avm is not None:
            if len(self._feats) == len(self._avm):
                feats = self._feats
            else:
                feats = list(self._avm)
            for feat in feats:
                val = self._avm[feat]
                try:
                    if val._is_notable():
                        fs.append((feat, val))
                    else:
                        for subfeat, subval in val.features():
                            fs.append(('{}.{}'.format(feat, subfeat), subval))
                except AttributeError:
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
