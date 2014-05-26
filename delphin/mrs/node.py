from collections import OrderedDict
from .lnk import LnkMixin
from .config import CVARSORT


class Node(LnkMixin):
    """
    A very simple predication for DMRSs. Nodes don't have |Arguments|
    or labels like |EPs|, but they do have a
    :py:attr:`~delphin.mrs.node.Node.carg` property for constant
    arguments, and their sortal type is given by the `cvarsort` value
    on their property mapping.

    Args:
        nodeid: node identifier
        pred: node's |Pred|
        sortinfo: node properties (with cvarsort)
        lnk: links pred to surface form or parse edges
        surface: surface string
        base: base form
        carg: constant argument string
    """

    def __init__(self, nodeid, pred, sortinfo=None,
                 lnk=None, surface=None, base=None, carg=None):
        self.nodeid = int(nodeid) if nodeid is not None else None
        self.pred = pred
        # sortinfo is the properties plus cvarsort
        self.sortinfo = OrderedDict(sortinfo or [])
        self.lnk = lnk
        self.surface = surface
        self.base = base
        self.carg = carg
        # accessor method
        self.get_property = self.sortinfo.get

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return 'Node({}[{}])'.format(self.nodeid, self.pred)

    def __eq__(self, other):
        # not doing self.__dict__ == other.__dict__ right now, because
        # functions like self.get_property show up there
        snid = self.nodeid
        onid = other.nodeid
        return ((None in (snid, onid) or snid == onid) and
                self.pred == other.pred and
                # make one side a regular dict for unordered comparison
                dict(self.sortinfo.items()) == other.sortinfo and
                self.lnk == other.lnk and
                self.surface == other.surface and
                self.base == other.base and
                self.carg == other.carg)

    @property
    def cvarsort(self):
        """
        The sortal type of the predicate.
        """
        return self.sortinfo.get(CVARSORT)

    @cvarsort.setter
    def cvarsort(self, value):
        self.sortinfo[CVARSORT] = value

    @property
    def properties(self):
        """
        The properties of the Node (without `cvarsort`, so it's the set
        of properties a corresponding |EP| would have).
        """
        return OrderedDict((k, v) for (k, v) in self.sortinfo.items()
                           if k != CVARSORT)

    def is_quantifier(self):
        """
        Return True if the Node is a quantifier, or False otherwise.
        """
        return self.pred.is_quantifier()