from .var import MrsVariable, AnchorMixin
from .config import (VARIABLE_ARG, HOLE_ARG, LABEL_ARG, HCONS_ARG,
                     CONSTANT_ARG, HANDLESORT)

class Argument(AnchorMixin):
    """
    An argument of an *MRS predicate.

    Args:
        nodeid: the nodeid of the node with the argument
        argname: the name of the argument (sometimes called "rargname")
        value: the MrsVariable or constant value of the argument
    """
    def __init__(self, nodeid, argname, value):
        self.nodeid = nodeid
        self.argname = argname
        self.value = value

    def __repr__(self):
        return 'Argument({nodeid} {argname}={value})'\
               .format(**self.__dict__)

    def __eq__(self, other):
        # ignore missing nodeid?
        # argname is case insensitive
        return (None in (self.nodeid, other.nodeid) or \
                self.nodeid == other.nodeid) and \
               self.argname.lower() == other.argname.lower() and \
               self.value == other.value

    @classmethod
    def mrs_argument(cls, argname, value):
        return cls(None, argname, value)

    @classmethod
    def rmrs_argument(cls, anchor, argname, value):
        return cls(anchor.vid, argname, value)

    @property
    def type(self):
        if isinstance(self.value, MrsVariable):
            if self.value.sort == HANDLESORT:
                # can't tell the diff between LABEL_ARG and HCONS_ARG
                # without the rest of the MRS, so just return HOLE_ARG
                return HOLE_ARG
            else:
                return VARIABLE_ARG
        else:
            return CONSTANT_ARG
