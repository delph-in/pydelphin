import re
from collections import OrderedDict
from .config import (HANDLESORT, CVARSORT, ANCHOR_SORT)

class MrsVariable(object):
    """A variable has an id (vid), sort, and maybe properties."""

    def __init__(self, vid, sort, properties=None):
        # vid is the number of the name (e.g. 1, 10003)
        self.vid        = int(vid)
        # sort is the letter(s) of the name (e.g. h, x)
        self.sort       = sort
        if sort == HANDLESORT and properties:
            pass # handles cannot have properties. Log this?
        self.properties = properties or OrderedDict()

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

    def __hash__(self):
        return hash(self.vid)

    def __repr__(self):
        return 'MrsVariable({}{})'.format(self.sort, self.vid)

    def __str__(self):
        return '{}{}'.format(str(self.sort), str(self.vid))

    @property
    def sortinfo(self):
        #FIXME: currently gets CVARSORT even if the var is not a CV
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

sort_vid_re = re.compile(r'^(\w*\D)(\d+)$')
def sort_vid_split(vs):
    return sort_vid_re.match(vs).groups()
