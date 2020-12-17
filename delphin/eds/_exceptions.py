
from delphin.exceptions import (
    PyDelphinException,
    PyDelphinSyntaxError,
    PyDelphinWarning,
)


class EDSError(PyDelphinException):
    """Raises on invalid EDS operations."""


class EDSSyntaxError(PyDelphinSyntaxError):
    """Raised when an invalid EDS string is encountered."""


class EDSWarning(PyDelphinWarning):
    """Issued when an EDS may be incorrect or incomplete."""
