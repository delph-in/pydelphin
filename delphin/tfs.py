"""
Basic classes for modeling Typed Feature Structures.

This module defines the TypedFeatureStructure class, which models an
attribute value matrix (AVM) with a type. It allows one to access
features through TDL-style dot notation, or through regular dictionary
access.
"""

class TypedFeatureStructure(object):

    __slots__ = ['_type', '_avm']

    def __init__(self, type, featvals=None):
        self._type = type
        self._avm = {}
        if isinstance(featvals, dict):
            featvals = featvals.items()
        for feat, val in list(featvals or []):
            self[feat] = val

    @classmethod
    def default(cls): return cls(None)

    def __repr__(self):
        return '<TypedFeatureStructure object ({}) at {}>'.format(
            self.type, id(self)
        )

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

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        self._type = value

    def get(self, key, default=None):
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
