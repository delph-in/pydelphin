
class XmrsError(Exception):
    pass


class XmrsSerializationError(XmrsError):
    pass


class XmrsDeserializationError(XmrsError):
    pass


class XmrsStructureError(XmrsError):
    pass


class MrsDecodeError(XmrsError):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.__str__()
        