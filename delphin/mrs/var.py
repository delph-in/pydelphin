import re
from collections import OrderedDict
from .config import (HANDLESORT, CVARSORT, ANCHOR_SORT)


sort_vid_re = re.compile(r'^(\w*\D)(\d+)$')


def sort_vid_split(vs):
    return sort_vid_re.match(vs).groups()


class MrsVariable(object):
    """An MrsVariable has an id (vid), sort, and sometimes properties.

    MrsVariables combine an integer variable ID (or *vid*)) with a
    string sortal type (*sort*). In MRS and RMRS, variables may be the
    bearers of the properties of an |EP| (thus the name "variable
    properties"). MrsVariables are used for several purposes:
    
    * **characteristic variables** (aka CVs)
    * **handles** (labels or holes)
    * **anchors** (a nodeid with a sort)
    * **variable argument values** (CVs, labels, holes, or
      underspecified variables for unexpressed arguments)

    Example:

    Within an Xmrs structure, a *vid* must be unique. MrsVariables
    can then be compared using either the sort and the vid or the vid
    by itself. For example, ``v1`` and ``v2`` below are not equal
    despite having the same vid (so they should not appear in the same
    Xmrs structure), but they are both equal to their shared vid of
    ``1``. Also note that an MrsVariable can be compared to its string
    representation.

    >>> v1 = MrsVariable(vid=1, sort='x')
    >>> v2 = MrsVariable(vid=1, sort='e')
    >>> v1 == v2
    False
    >>> v1 == 1
    True
    >>> v2 == 1
    True
    >>> v1 == 'x1'
    True
    >>> v1 == 'x2'
    False
    >>> v1 == 'e1'
    False

    Args:
        vid: an number for the variable ID
        sort: a string for the sortal type
        properties: a dictionary of variable properties
    Returns:
        an instantiated MrsVariable object
    Raises:
        ValueError: when *vid* is not castable to an int
    """
    def __init__(self, vid, sort, properties=None):
        # vid is the number of the name (e.g. 1, 10003)
        self.vid = int(vid)
        # sort is the letter(s) of the name (e.g. h, x)
        self.sort = sort
        if sort == HANDLESORT and properties:
            pass  # handles cannot have properties. Log this?
        self.properties = properties or OrderedDict()

    @classmethod
    def from_string(cls, varstring):
        """
        Construct an |MrsVariable| by its string representation.

        Args:
            varstring: a string containing the sort and vid of an
                MrsVariable, such as "x1" or "event3"
        Returns:
            an instantiated MrsVariable object if the string represents
            an MrsVariable, or None otherwise
        """
        srt_vid = sort_vid_split(varstring)
        if srt_vid:
            sort, vid = srt_vid
            return cls(vid, sort)
        return None

    def __eq__(self, other):
        if isinstance(other, MrsVariable):
            return self.vid == other.vid and self.sort == other.sort
        else:
            # it could be a vid like 1 or '1'
            try:
                return self.vid == int(other)
            # or a string like 'x1'
            except ValueError:
                return str(self) == other
            # other is not an int nor a string
            except TypeError:
                return False

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return 'MrsVariable({}{})'.format(self.sort, self.vid)

    def __str__(self):
        return '{}{}'.format(str(self.sort), str(self.vid))

    @property
    def sortinfo(self):
        """
        Return the properties including a mapping of "cvarsort" to
        the sort of the MrsVariable. Sortinfo is used in DMRS objects,
        which don't have variables, in order to capture the sortal type
        of a |Node|.
        """
        # FIXME: currently gets CVARSORT even if the var is not a CV
        sortinfo = OrderedDict([(CVARSORT, self.sort)])
        sortinfo.update(self.properties)
        return sortinfo


# I'm not sure this belongs here, but anchors are MrsVariables...
class AnchorMixin(object):
    @property
    def anchor(self):
        if self.nodeid is not None:
            return MrsVariable(vid=self.nodeid, sort=ANCHOR_SORT)
        return None

    @anchor.setter
    def anchor(self, anchor):
        self.nodeid = anchor.vid


class VarGenerator(object):
    """Simple class to produce MrsVariables, incrementing the vid for
       each one."""

    def __init__(self, starting_vid=1):
        self.vid = starting_vid

    def new(self, sort, properties=None):
        v = MrsVariable(self.vid, sort, properties=properties)
        self.vid += 1
        return v
