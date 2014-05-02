from .var import MrsVariable, AnchorMixin
from .config import (CVARG, INTRINSIC_ARG, VARIABLE_ARG, HOLE_ARG,
                     LABEL_ARG, HCONS_ARG, CONSTANT_ARG, HANDLESORT)


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
        self._type = None

    def __repr__(self):
        return 'Argument({nodeid}:{argname}:{value})'\
               .format(**self.__dict__)

    def __eq__(self, other):
        # ignore missing nodeid?
        # argname is case insensitive
        snid = self.nodeid
        onid = other.nodeid
        return (
            (None in (snid, onid) or snid == onid) and
            self.argname.lower() == other.argname.lower() and
            self.value == other.value
        )

    @classmethod
    def mrs_argument(cls, argname, value):
        return cls(None, argname, value)

    @classmethod
    def rmrs_argument(cls, anchor, argname, value):
        return cls(anchor.vid, argname, value)

    def infer_argument_type(self, xmrs=None):
        if self.argname == CVARG:
            return INTRINSIC_ARG
        elif isinstance(self.value, MrsVariable):
            if self.value.sort == HANDLESORT:
                # if there's no xmrs given, then use HOLE_ARG as it
                # is the supertype of LABEL_ARG and HCONS_ARG
                if xmrs is not None:
                    if xmrs.get_hcons(self.value) is not None:
                        return HCONS_ARG
                    else:
                        return LABEL_ARG
                else:
                    return HOLE_ARG
            else:
                return VARIABLE_ARG
        else:
            return CONSTANT_ARG

    @property
    def type(self):
        if self._type is None:
            self._type = self.infer_argument_type()
        return self._type

    @type.setter
    def type(self, value):
        self._type = value