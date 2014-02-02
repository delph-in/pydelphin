
class Argument(object):
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

    @classmethod
    def mrs_argument(cls, argname, value):
        return cls(None, argname, value)

    @classmethod
    def rmrs_argument(cls, anchor, argname, value):
        return cls(anchor.vid, argname, value)

