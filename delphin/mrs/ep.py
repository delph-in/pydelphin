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
            args (list): the EP's Arguments
            lnk: Lnk object associated with the pred
            surface: surface string
            base: base form
        """
        self.label = label
        nodeid=anchor.vid if anchor else None
        # first args, then can get CV
        self.argdict  = OrderedDict((a.argname, a) for a in (args or []))
        sortinfo = self.cv.sortinfo if self.cv else None
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

    def arg_value(self, argname):
        try:
            arg = self.argdict[argname]
            return arg.value
        except KeyError:
            return None

    @property
    def anchor(self):
        return MrsVariable(vid=self.nodeid, sort=ANCHOR_SORT)

    @anchor.setter
    def anchor(self, anchor):
        self.nodeid = anchor.vid

    @property
    def cv(self):
        return self.arg_value(CVARG)

    @property
    def carg(self):
        return self.arg_value(CONSTARG)

    @property
    def args(self):
        return list(self.argdict.values())
