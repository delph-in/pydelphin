from collections import OrderedDict
from .lnk import LnkObject

class Node(LnkObject):
    """The base class for units of MRSs containing predicates and their
       properties."""
    def __init__(self, pred, nodeid,
                 properties=None, lnk=None,
                 surface=None, base=None, carg=None):
        self.pred       = pred      # mrs.Pred object
        self.nodeid     = nodeid    # RMRS anchor, DMRS nodeid, etc.
        self.properties = properties or OrderedDict()
        self.lnk        = lnk       # mrs.Lnk object
        self.surface    = surface
        self.base       = base      # here for compatibility with the DTD
        self.carg       = carg

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Node({}[{}])'.format(self.nodeid, self.pred)
