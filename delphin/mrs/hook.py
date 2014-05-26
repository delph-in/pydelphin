
class Hook(object):
    """
    A container class for LTOP, INDEX, and XARG.

    This class simply encapsulates three variables associated with an
    |Xmrs| object, and none of the arguments are required.

    Args:
        ltop: the global top handle
        index: the semantic index
        xarg: the external argument (not likely used for a full |Xmrs|)
    """
    def __init__(self, ltop=None, index=None, xarg=None):
        self.ltop = ltop
        self.index = index
        self.xarg = xarg

    def __repr__(self):
        return 'Hook(ltop={} index={} xarg={})'.format(
            self.ltop, self.index, self.xarg
        )