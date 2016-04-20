
class PyDelphinException(Exception): pass
class PyDelphinWarning(Warning): pass

class ItsdbError(PyDelphinException): pass

class XmrsError(PyDelphinException): pass
class XmrsSerializationError(XmrsError): pass
class XmrsDeserializationError(XmrsError): pass
class XmrsStructureError(XmrsError): pass
class XmrsWarning(PyDelphinWarning): pass

class TdlError(PyDelphinException): pass

class TdlParsingError(TdlError):
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
