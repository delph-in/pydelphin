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
        self.nodeid     = nodeid    # DMRS-style nodeid
        self.pred       = pred      # mrs.Pred object
        # sortinfo is the properties plus cvarsort
        self.sortinfo   = sortinfo or OrderedDict()
        self.lnk        = lnk       # mrs.Lnk object
        self.surface    = surface
        self.base       = base      # here for compatibility with the DTD
        self.carg       = carg

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Node({}[{}])'.format(self.nodeid, self.pred)

    def __eq__(self, other):
        return self.nodeid == other.nodeid and \
                self.pred == other.pred and \
                set(self.sortinfo.items()) == set(other.sortinfo.items()) and \
                self.lnk == other.lnk

    @property
    def cvarsort(self):
        return self.sortinfo.get(CVARSORT)

    @property
    def properties(self):
        return OrderedDict((k,v) for (k,v) in self.sortinfo.items()
                           if k != CVARSORT)

    def is_quantifier(self):
        return self.pred.is_quantifier()
