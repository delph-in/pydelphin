from collections import OrderedDict
from .lnk import LnkMixin
from .node import Node
from .config import (CVARG, CONSTARG)

class ElementaryPredication(LnkMixin):
    """
    An elementary predication (EP) is an extension of a Node that
    requires a characteristic variable (cv) and label.
    """
    def __init__(self, pred, label, anchor=None, args=None,
                 lnk=None, surface=None, base=None):
        """
        Args:
            pred (Pred): EP's predicate
            label (MrsVariable): label handle
            anchor (MrsVariable): the RMRS anchor (similar to a nodeid)
            args (list): the EP's Arguments (argname, value)
            lnk: Lnk object associated with the pred
            surface: surface string
            base: base form
        """
        # first args, then can get CV
        self.argdict  = OrderedDict(args or [])
        sortinfo = self.cv.sortinfo if self.cv else None
        self.label = label
        nodeid=anchor.vid if anchor else None
        self._node = Node(nodeid, pred, sortinfo=sortinfo, lnk=lnk,
                          surface=surface, base=base, carg=self.carg)
        # copy up the following from _node
        self.nodeid        = self._node.nodeid
        self.pred          = self._node.pred
        self.sortinfo      = self._node.sortinfo
        self.properties    = self._node.properties
        self.lnk           = self._node.lnk
        self.surface       = self._node.surface
        self.base          = self._node.base
        #self.carg          = self._node.carg
        self.cvarsort      = self._node.cvarsort
        self.is_quantifier = self._node.is_quantifier

    def __repr__(self):
        return 'ElementaryPredication({}[{}])'.format(str(self.pred),
                                                      str(self.cv or '?'))

    def __str__(self):
        return self.__repr__()

    @property
    def cv(self):
        return self.argdict.get(CVARG)

    @property
    def carg(self):
        return self.argdict.get(CONSTARG)

    @property
    def args(self):
        return list(self.argdict.items())
