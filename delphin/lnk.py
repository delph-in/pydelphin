"""
Surface alignment for semantic entities.
"""

__all__ = [
    "Lnk",
    "LnkError",
    "LnkMixin",  # noqa: F822 ; for backward compatibility
]

import warnings
from collections.abc import Iterable
from typing import Any, overload

from delphin.__about__ import __version__  # noqa: F401
from delphin.exceptions import PyDelphinException, PyDelphinWarning


class LnkError(PyDelphinException):
    """Raised on invalid Lnk values or operations."""


class Lnk:
    """
    Surface-alignment information for predications.

    Lnk objects link predicates to the surface form in one of several
    ways, the most common of which being the character span of the
    original string.

    Valid types and their associated *data* shown in the table below.

    =============  ===================  =========
    type           data                 example
    =============  ===================  =========
    Lnk.CHARSPAN   surface string span  (0, 5)
    Lnk.CHARTSPAN  chart vertex span    (0, 5)
    Lnk.TOKENS     token identifiers    (0, 1, 2)
    Lnk.EDGE       edge identifier      1
    =============  ===================  =========

    Args:
        arg: Lnk type or the string representation of a Lnk
        data: alignment data (assumes *arg* is a Lnk type)
    Attributes:
        type: the way the Lnk relates the semantics to the surface form
        data: the alignment data (depends on the Lnk type)

    Example:

        >>> Lnk("<0:5>").data
        (0, 5)
        >>> str(Lnk.charspan(0, 5))
        '<0:5>'
        >>> str(Lnk.chartspan(0, 5))
        '<0#5>'
        >>> str(Lnk.tokens([0, 1, 2]))
        '<0 1 2>'
        >>> str(Lnk.edge(1))
        '<@1>'
    """

    __slots__ = ("type", "_data")

    type: int
    _data: tuple[int, ...]

    # These types determine how a lnk on an EP or MRS are to be
    # interpreted, and thus determine the data type/structure of the
    # lnk data.
    UNSPECIFIED = 0
    CHARSPAN = 1  # Character span; a pair of offsets
    CHARTSPAN = 2  # Chart vertex span: a pair of indices
    TOKENS = 3  # Token numbers: a list of indices
    EDGE = 4  # An edge identifier: a number

    @overload
    def __init__(self, arg: str, data: None = None) -> None: ...

    @overload
    def __init__(
        self,
        arg: int,
        data: None | int | tuple[int, ...] = None,
    ) -> None: ...

    def __init__(
        self,
        arg: str | int,
        data: None | int | tuple[int, ...] = None,
    ) -> None:
        if isinstance(arg, str):
            if data is not None:
                raise LnkError("data argument should be None when arg is a string")
            if (arg[:1], arg[-1:]) != ("<", ">"):
                raise LnkError(f"invalid Lnk string: {arg!r}")
            arg = arg[1:-1]
            if arg.startswith("@"):
                self.type = Lnk.EDGE
                self._data = (int(arg[1:]),)
            elif ":" in arg:
                cfrom, cto = arg.split(":")
                self.type = Lnk.CHARSPAN
                self._data = (int(cfrom), int(cto))
            elif "#" in arg:
                vfrom, vto = arg.split("#")
                self.type = Lnk.CHARTSPAN
                self._data = (int(vfrom), int(vto))
            else:
                self.type = Lnk.TOKENS
                self._data = tuple(map(int, arg.split()))
        elif isinstance(arg, int):
            if arg not in (
                Lnk.UNSPECIFIED,
                Lnk.CHARSPAN,
                Lnk.CHARTSPAN,
                Lnk.TOKENS,
                Lnk.EDGE,
            ):
                raise LnkError(f"invalid Lnk type {arg!r}")
            self.type = arg
            match data:
                case tuple():
                    self._data = data
                case int():
                    self._data = (data,)
                case None:
                    self._data = ()
                case _:
                    raise LnkError(f"invalid Lnk data: f{data}")
        else:
            raise LnkError(f"invalid Lnk: {(arg, data)!r}")

    @classmethod
    def default(cls):
        """
        Create a Lnk object for when no information is given.
        """
        return cls(Lnk.UNSPECIFIED)

    @classmethod
    def charspan(cls, start: str | int, end: str | int):
        """
        Create a Lnk object for a character span.

        Args:
            start: the initial character position (cfrom)
            end: the final character position (cto)
        """
        return cls(Lnk.CHARSPAN, (int(start), int(end)))

    @classmethod
    def chartspan(cls, start: str | int, end: str | int):
        """
        Create a Lnk object for a chart span.

        Args:
            start: the initial chart vertex
            end: the final chart vertex
        """
        return cls(Lnk.CHARTSPAN, (int(start), int(end)))

    @classmethod
    def tokens(cls, tokens: Iterable[str | int]):
        """
        Create a Lnk object for a token range.

        Args:
            tokens: a list of token identifiers
        """
        return cls(Lnk.TOKENS, tuple(map(int, tokens)))

    @classmethod
    def edge(cls, edge: str | int):
        """
        Create a Lnk object for an edge (used internally in generation).

        Args:
            edge: an edge identifier
        """
        return cls(Lnk.EDGE, int(edge))

    @property
    def data(self) -> int | tuple[int, ...] | None:
        match self.type:
            case Lnk.UNSPECIFIED:
                return None
            case Lnk.CHARSPAN | Lnk.CHARTSPAN | Lnk.TOKENS:
                return self._data
            case Lnk.EDGE:
                if len(self._data) != 1:
                    raise LnkError(f"invalid data for edge-type Lnk: {self._data}")
                return self._data[0]
            case _:
                raise LnkError("invalid Lnk type")

    def __str__(self) -> str:
        match self.type:
            case Lnk.UNSPECIFIED:
                return ""
            case Lnk.CHARSPAN:
                return f"<{self._data[0]}:{self._data[1]}>"
            case Lnk.CHARTSPAN:
                return f"<{self._data[0]}#{self._data[1]}>"
            case Lnk.EDGE:
                return f"<@{self._data[0]}>"
            case Lnk.TOKENS:
                return "<{}>".format(" ".join(map(str, self._data)))
            case _:
                raise LnkError("invalid Lnk type")

    def __repr__(self):
        return f"<Lnk object {self!s} at {id(self)}>"

    def __eq__(self, other):
        return self.type == other.type and self._data == other._data

    def __bool__(self):
        if self.type == Lnk.UNSPECIFIED:
            return False
        if self.type == Lnk.CHARSPAN and self._data == (-1, -1):
            return False
        return True


# LnkMixin has been moved to delphin.sembase. To keep backward
# compatibility and avoid circular imports, load it only when
# requested.


def __getattr__(name: str) -> Any:
    if name == "LnkMixin":
        from delphin.sembase import LnkMixin

        warnings.warn(
            "LnkMixin has been moved to delphin.sembase.LnkMixin",
            PyDelphinWarning,
            stacklevel=2,
        )
        return LnkMixin
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
