
class PyDelphinException(Exception):
    """The base class for pyDelphin exceptions."""
    def __init__(self, *args, **kwargs):
        """Create a new PyDelphinException."""
        return super(PyDelphinException, self).__init__(*args, **kwargs)

class PyDelphinWarning(Warning):
    """The base class for pyDelphin warnings."""
    def __init__(self, *args, **kwargs):
        """Create a new PyDelphinWarning."""
        return super(PyDelphinWarning, self).__init__(*args, **kwargs)


class ItsdbError(PyDelphinException):
    """Raised when there is an error processing a [incr tsdb()] profile."""
    pass


class XmrsError(PyDelphinException):
    """Raised when there is an error processing *MRS objects."""
    pass

class XmrsSerializationError(XmrsError):
    """Raised when serializing *MRS objects fails."""
    pass

class XmrsDeserializationError(XmrsError):
    """Raised when deserializing *MRS objects fails."""
    pass

class XmrsStructureError(XmrsError):
    """Raised when a *MRS object is structurally ill-formed."""
    pass

class XmrsWarning(PyDelphinWarning):
    """Warning class for *MRS processing."""
    pass


class TdlError(PyDelphinException):
    """Raised when there is an error in processing TDL."""
    pass

class TdlParsingError(TdlError):
    """Raised when parsing TDL text fails."""
    
    def __init__(self, *args, **kwargs):
        # Python2 doesn't allow parameters like:
        #   (*args, key=val, **kwargs)
        # so do this manaully.
        filename = line_number = identifier = None
        if 'filename' in kwargs:
            filename = kwargs['filename']
            del kwargs['filename']
        if 'line_number' in kwargs:
            line_number = kwargs['line_number']
            del kwargs['line_number']
        if 'identifier' in kwargs:
            identifier = kwargs['identifier']
            del kwargs['identifier']

        TdlError.__init__(self, *args, **kwargs)
        self.filename = filename
        self.line_number = line_number
        self.identifier = identifier

    def __str__(self):
        return 'At {}:{} ({})\n{}'.format(
            self.filename or '?',
            self.line_number or '?',
            self.identifier or 'type/rule definition',
            TdlError.__str__(self)
        )
