
class PyDelphinException(Exception):
    pass


class ItsdbError(PyDelphinException):
    pass


class XmrsError(PyDelphinException):
    pass


class XmrsSerializationError(XmrsError):
    pass


class XmrsDeserializationError(XmrsError):
    pass


class XmrsStructureError(XmrsError):
    pass

class TdlError(PyDelphinException):
    pass

class TdlParsingError(TdlError):
    def __init__(self, *args, filename=None, line_number=None, identifier=None,
                 **kwargs):
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