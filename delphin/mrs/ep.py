from collections import OrderedDict
from .node import Node

class ElementaryPredication(Node):
    """An elementary predication (EP) is an extension of a Node that
       requires a characteristic variable (cv) and label. Arguments are
       optional, so this class can be used for EPs in both MRS and RMRS."""
    def __init__(self, pred, nodeid, label, cv, args=None,
                 lnk=None, surface=None, base=None, carg=None):
        Node.__init__(self, pred, nodeid,
                      properties=cv.properties if cv is not None else None,
                      lnk=lnk, surface=surface, base=base, carg=carg)
        self.label  = label
        self.cv     = cv    # characteristic var (bound var for quantifiers)
        self.args   = args if args is not None else OrderedDict()

    def __len__(self):
        """Return the length of the EP, which is the number of args."""
        return len(self.args)

    def __repr__(self):
        return 'ElementaryPredication({}[{}])'.format(str(self.pred),
                                                      str(self.cv or '?'))

    def __str__(self):
        return self.__repr__()

    def is_quantifier(self):
        return self.pred.pos == 'q'
