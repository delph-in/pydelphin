

class TypedFeatureStructure(object):

    __slots__ = ['_type', '_avm']

    def __init__(self, type, featvals=None):
        self._type = type
        self._avm = {}
        if isinstance(featvals, dict):
            featvals = featvals.items()
        for feat, val in list(featvals or []):
            self[feat] = val

    def __repr__(self):
        return '<TypedFeatureStructure object ({}) at {}>'.format(
            self.type, id(self)
        )

    def __setitem__(self, key, val):
        try:
            first, rest = key.split('.', 1)
        except ValueError:
            self._avm[key.upper()] = val
        else:
            first = first.upper()  # features are case-insensitive
            try:
                subdef = self._avm[first]
            except KeyError:
                # use type(self) so it still works with inherited classes
                subdef = self._avm.setdefault(first, type(self)())
            subdef[rest] = val

    def __getitem__(self, key):
        try:
            first, rest = key.split('.', 1)
        except ValueError:
            return self._avm[key.upper()]
        else:
            return self._avm[first.upper()][rest]

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
            return default

    def _is_notable(self):
        """
        Notability determines if the TFS should be listed as the value
        of a feature or if the feature should just "pass through" its
        avm to get the next value. A notable TypedFeatureStructure is
        one without any other features (i.e. an empty AVM)
        """
        return not self._avm

    def features(self):
        for feat, val in self._avm.items():
            try:
                if val._is_notable():
                    yield (feat, val)
                else:
                    for subfeat, subval in val.features():
                        yield ('{}.{}'.format(feat, subfeat), subval)
            except AttributeError:
                yield (feat, val)

