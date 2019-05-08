
from delphin.exceptions import PyDelphinException, PyDelphinSyntaxError


class EDSError(PyDelphinException):
    """Raises on invalid EDS operations."""


class EDSSyntaxError(PyDelphinSyntaxError):
    """Raised when an invalid EDS string is encountered."""
