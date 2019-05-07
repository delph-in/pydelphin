
from delphin.exceptions import PyDelphinException, PyDelphinSyntaxError


class MRSError(PyDelphinException):
    """Raises on invalid MRS operations."""


class MRSSyntaxError(PyDelphinSyntaxError):
    """Raised when an invalid MRS serialization is encountered."""
