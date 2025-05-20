
"""
Basic classes for modeling feature structures.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Callable, Iterable, Optional, Union

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401
from delphin.exceptions import PyDelphinException
from delphin.hierarchy import MultiHierarchy


class TFSError(PyDelphinException):
    """Raised on invalid feature structure operations."""


# generic input argument types
FeatureSeq = Sequence[tuple[str, Any]]
FeatureMap = Mapping[str, Any]
# explicit types
FeatureList = list[tuple[str, Any]]
FeatureDict = dict[str, Any]


class FeatureStructure:
    """
    A feature structure.

    This class manages the access of nested features using
    dot-delimited notation (e.g., `SYNSEM.LOCAL.CAT.HEAD`).

    Args:
        featvals (dict, list): a mapping or iterable of feature paths
            to feature values
    """

    __slots__ = '_avm',

    _avm: FeatureDict

    def __init__(
        self,
        featvals: Union[FeatureSeq, FeatureMap, None] = None,
    ) -> None:
        self._avm = {}
        if featvals and hasattr(featvals, 'items'):
            featvals = list(featvals.items())
        for feat, val in list(featvals or []):
            self[feat] = val

    @classmethod
    def _default(cls) -> 'FeatureStructure':
        return cls(None)

    def __repr__(self) -> str:
        return '<{} object at {}>'.format(self.__class__.__name__, id(self))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, FeatureStructure):
            return NotImplemented
        return self._avm == other._avm

    def __setitem__(self, key: str, val: Any) -> None:
        avm = self._avm
        subkey, _, rest = key.partition(".")
        subkey = subkey.upper()
        if not rest:
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
            subdef[rest] = val

    def __getitem__(self, key: str) -> Any:
        first, _, remainder = key.partition('.')
        val = self._avm[first.upper()]
        if remainder:
            val = val[remainder]
        return val

    def __delitem__(self, key: str) -> None:
        first, _, remainder = key.partition('.')
        if remainder:
            fs = self._avm[first.upper()]
            del fs[remainder]
        else:
            del self._avm[first.upper()]

    def __contains__(self, key: str) -> bool:
        subkeys = key.split('.', 1)
        subkey = subkeys[0].upper()
        if subkey in self._avm:
            if len(subkeys) == 2:
                return subkeys[1] in self._avm[subkey]
            else:
                return True
        return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Return the value for *key* if it exists, otherwise *default*.
        """
        try:
            val = self[key]
        except KeyError:
            val = default
        return val

    def _is_notable(self) -> bool:
        """
        Notability determines if the FeatureStructure should be listed as
        the value of a feature or if the feature should just "pass
        through" its avm to get the next value. A notable
        FeatureStructure is one with more than one sub-feature.
        """
        return self._avm is None or len(self._avm) != 1

    def features(self, expand: bool = False) -> FeatureList:
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
            for feat, val in self._avm.items():
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

    _type: str

    def __init__(
        self,
        type: str,
        featvals: Union[FeatureSeq, FeatureMap, None] = None,
    ) -> None:
        self._type = type
        super().__init__(featvals)

    def __repr__(self) -> str:
        return '<TypedFeatureStructure object ({}) at {}>'.format(
            self.type, id(self)
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TypedFeatureStructure):
            return NotImplemented
        return self._type == other._type and self._avm == other._avm

    @property
    def type(self) -> str:
        """The type assigned to the feature structure."""
        return self._type

    @type.setter
    def type(self, value: str) -> None:
        self._type = value


class TypeHierarchy(MultiHierarchy[str]):
    """
    A Type Hierarchy.

    Type hierarchies are instances of
    :class:`delphin.hierarchy.MultiHierarchy` constrained to use
    case-insensitive (downcased) strings for node identifiers and
    unique greatest-lower-bound (glb) types.

    Note:
        Checks for unique glbs is not yet implemented.

    >>> th = TypeHierarchy(
    ...     '*top*',
    ...     {'can-fly': '*top*', 'can-swim': '*top*', 'can-walk': '*top*'}
    ... )
    >>> th.update({'butterfly': ('can-fly', 'can-walk')})
    >>> th['butterfly'] = 'some info relating to butterflies'
    >>> th.update(
    ...     {'duck': ('can-fly', 'can-swim', 'can-walk')},
    ...     data={'duck': 'some info relating to ducks...'}
    ... )

    """

    def __init__(
        self,
        top: str,
        hierarchy: Optional[Mapping[str, Iterable[str]]] = None,
        data: Optional[Mapping[str, Any]] = None,
        normalize_identifier: Optional[Callable[[str], str]] = None
    ) -> None:
        if not normalize_identifier:
            normalize_identifier = str.lower
        super().__init__(
            top,
            hierarchy=hierarchy,
            data=data,
            normalize_identifier=normalize_identifier
        )
