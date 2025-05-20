from delphin.exceptions import (
    PyDelphinException,
    PyDelphinSyntaxError,
    PyDelphinWarning,
)


class TDLError(PyDelphinException):
    """Raised when there is an error in processing TDL."""


class TDLSyntaxError(PyDelphinSyntaxError):
    """Raised when parsing TDL text fails."""


class TDLWarning(PyDelphinWarning):
    """Raised when parsing unsupported TDL features."""
