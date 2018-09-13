"""
Basic classes for modeling feature structures.

This module defines the :class:`FeatureStructure` and
:class:`TypedFeatureStructure` classes, which model an attribute value
matrix (AVM), with the latter including an associated type. They allow
feature access through TDL-style dot notation regular dictionary keys.

"""

class TypedFeatureStructure(object):
    """
    A typed :class:`FeatureStructure`.

    Args:
        type (str): type name
        featvals (dict, list): a mapping or iterable of feature paths
            to feature values
    """
    __slots__ = ['_type', '_avm']

    def __init__(self, type, featvals=None):
        self._type = type
        super(TypedFeatureStructure, self).__init__(self, featvals)

    def __repr__(self):
        return '<TypedFeatureStructure object ({}) at {}>'.format(
            self.type, id(self)
        )

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        self._type = value


class FeatureStructure(object):
    """
    A feature structure.

    This class manages the access of nested features using
    dot-delimited notation (e.g., `SYNSEM.LOCAL.CAT.HEAD`).

    Args:
        featvals (dict, list): a mapping or iterable of feature paths
            to feature values
    """

    __slots__ = ['_avm']

    def __init__(self, featvals=None):
        self._avm = {}
        if isinstance(featvals, dict):
            featvals = featvals.items()
        for feat, val in list(featvals or []):
            self[feat] = val

    @classmethod
    def default(cls): return cls(None)

    def __repr__(self):
        return '<FeatureStructure object at {}>'.format(id(self))

    def __setitem__(self, key, val):
        subkeys = key.split('.', 1)
        subkey = subkeys[0].upper()
        if len(subkeys) == 1:
            self._avm[subkey] = val
        else:
            if subkey in self._avm:
                subdef = self._avm[subkey]
            else:
                subdef = self._avm[subkey] = self.default()
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
        Notability determines if the TFS should be listed as the value
        of a feature or if the feature should just "pass through" its
        avm to get the next value. A notable TypedFeatureStructure is
        one with more than one sub-feature.
        """
        return len(self._avm) != 1

    def features(self):
        """
        Return the list of tuples of feature paths and feature values.
        """
        fs = []
        for feat, val in self._avm.items():
            try:
                if val._is_notable():
                    fs.append((feat, val))
                else:
                    for subfeat, subval in val.features():
                        fs.append(('{}.{}'.format(feat, subfeat), subval))
            except AttributeError:
                fs.append((feat, val))
        return fs
