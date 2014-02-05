from collections import OrderedDict
from .lnk import LnkMixin
from .config import CVARSORT

class Node(LnkMixin):
    """The base class for units of MRSs containing predicates and their
       properties."""
    def __init__(self, nodeid, pred, sortinfo=None,
                 lnk=None, surface=None, base=None, carg=None):
        """
        Args:
            nodeid (int): node identifier
            pred (Pred): node's predicate
            sortinfo (OrderedDict): node properties (with cvarsort)
            lnk (Lnk): links pred to surface form or parse edges
            surface: surface string
            base: base form
            carg: constant argument string
        Returns:
            a Node object
        """
        self.nodeid     = int(nodeid) if nodeid is not None else None
        self.pred       = pred
        # sortinfo is the properties plus cvarsort
        self.sortinfo   = OrderedDict(sortinfo or [])
        self.lnk        = lnk
        self.surface    = surface
        self.base       = base
        self.carg       = carg
        # accessor method
        self.get_property = self.sortinfo.get

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Node({}[{}])'.format(self.nodeid, self.pred)

    def __eq__(self, other):
        # not doing self.__dict__ == other.__dict__ right now, because
        # functions like self.get_property show up there
        return (None in (self.nodeid, other.nodeid) or \
                self.nodeid == other.nodeid) and \
               self.pred == other.pred and \
               sorted(self.sortinfo.items()) == sorted(other.sortinfo.items()) and \
               self.lnk == other.lnk and \
               self.surface == other.surface and \
               self.base == other.base and \
               self.carg == other.carg

    @property
    def cvarsort(self):
        return self.sortinfo.get(CVARSORT)
    @cvarsort.setter
    def cvarsort(self, value):
        self.sortinfo[CVARSORT] = value

    @property
    def properties(self):
        return OrderedDict((k,v) for (k,v) in self.sortinfo.items()
                           if k != CVARSORT)

    def is_quantifier(self):
        return self.pred.is_quantifier()