from collections import OrderedDict
from .node import Node
from .lnk import LnkMixin
from .var import (MrsVariable, AnchorMixin)
from .config import (CVARG, CONSTARG, ANCHOR_SORT)

class ElementaryPredication(LnkMixin, AnchorMixin):
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
        # first args, then can get CV
        self.argdict  = OrderedDict((a.argname, a) for a in (args or []))
        # Only fill in other attributes if pred is given, otherwise ignore.
        # This behavior is to help enable the from_node classmethod.
        self._node = None
        if pred is not None:
            cv = self.cv
            self._node = Node(
                anchor.vid if anchor else None,
                pred,
                sortinfo=cv.sortinfo if cv else None,
                lnk=lnk,
                surface=surface,
                base=base,
                carg=self.carg
            )

    @classmethod
    def from_node(cls, label, node, args=None):
        ep = cls(None, label, args=args)
        ep._node = node
        return ep

    def __repr__(self):
        return 'ElementaryPredication({}[{}])'.format(str(self.pred),
                                                      str(self.cv or '?'))

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.label == other.label and \
               self.argdict == other.argdict and \
               self._node == other._node

    # these properties provide an interface to the node attributes

    @property
    def nodeid(self):
        return self._node.nodeid
    @nodeid.setter
    def nodeid(self, value):
        self._node.nodeid = value
    
    @property
    def pred(self):
        return self._node.pred
    @pred.setter
    def pred(self, value):
        self._node.pred = value
    
    @property
    def lnk(self):
        return self._node.lnk
    @lnk.setter
    def lnk(self, value):
        self._node.lnk = value
    
    @property
    def surface(self):
        return self._node.surface
    @surface.setter
    def surface(self, value):
        self._node.surface = value
    
    @property
    def base(self):
        return self._node.base
    @base.setter
    def base(self, value):
        self._node.base = value
    
    # carg property intentionally left out. It should be accessed from
    # the arg list (see the property below)

    # these properties are specific to the EP's qualities

    @property
    def cv(self):
        return self.arg_value(CVARG)

    @property
    def properties(self):
        try:
            return self.cv.properties
        except AttributeError: # in case cv is None
            return OrderedDict()

    @property
    def carg(self):
        return self.arg_value(CONSTARG)

    @property
    def args(self):
        return list(self.argdict.values())

    def arg_value(self, argname):
        try:
            arg = self.argdict[argname]
            return arg.value
        except KeyError:
            return None