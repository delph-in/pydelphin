
"""
Basic exception and warning classes for PyDelphin.
"""

# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


class PyDelphinException(Exception):
    """The base class for PyDelphin exceptions."""
    def __init__(self, *args, **kwargs):
        super(PyDelphinException, self).__init__(*args, **kwargs)


class PyDelphinWarning(Warning):
    """The base class for PyDelphin warnings."""
    def __init__(self, *args, **kwargs):
        super(PyDelphinWarning, self).__init__(*args, **kwargs)


class PyDelphinSyntaxError(PyDelphinException):
    def __init__(self, message=None, filename=None,
                 lineno=None, offset=None, text=None):
        self.message = message
        self.filename = filename
        self.lineno = lineno
        self.offset = offset
        self.text = text

    def __str__(self):
        parts = []
        if self.filename is not None:
            parts.append('File "{}"'.format(self.filename))
        if self.lineno is not None:
            parts.append('line {}'.format(self.lineno))
        if parts:
            parts = ['', '  ' + ', '.join(parts)]
        if self.text is not None:
            parts.append('    ' + self.text)
            if self.offset is not None:
                parts.append('   ' + (' ' * self.offset) + '^')
        elif parts:
            parts[-1] += ', character {}'.format(self.offset)
        if self.message is not None:
            parts.append('{}: {}'.format(self.__class__.__name__,
                                         self.message))
        return '\n'.join(parts)
