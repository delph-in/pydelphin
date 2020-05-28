
from delphin.exceptions import (
    PyDelphinException,
    PyDelphinSyntaxError,
    PyDelphinWarning,
)


class DMRSError(PyDelphinException):
    """Raises on invalid DMRS operations."""


class DMRSSyntaxError(PyDelphinSyntaxError):
    """Raised when an invalid DMRS serialization is encountered."""


class DMRSWarning(PyDelphinWarning):
    """Issued when a DMRS may be incorrect or incomplete."""
