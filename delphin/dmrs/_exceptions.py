
from delphin.exceptions import PyDelphinException, PyDelphinSyntaxError


class DMRSError(PyDelphinException):
    """Raises on invalid DMRS operations."""


class DMRSSyntaxError(PyDelphinSyntaxError):
    """Raised when an invalid DMRS serialization is encountered."""
