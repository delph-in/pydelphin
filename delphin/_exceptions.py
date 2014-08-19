
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
