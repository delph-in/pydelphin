import re

class MrsVariable(object):
    """A variable has a variable type and properties."""

    def __init__(self, sort, vid, properties=None):
        self.sort       = sort  # sort is the letter(s) of the name (e.g. h, x)
        self.vid        = vid   # vid is the number of the name (e.g. 1, 10003)
        if sort == 'h' and properties:
            pass # handles cannot have properties. Log this?
        self.properties = properties #TODO: consider removing properties

    def __eq__(self, other):
        try:
            return self.sort == other.sort and self.vid == other.vid
        except AttributeError:
            return False

    def __hash__(self):
        return hash(str(self))

    def __repr__(self):
        return 'MrsVariable({}{})'.format(self.sort, self.vid)

    def __str__(self):
        return '{}{}'.format(str(self.sort), str(self.vid))

class VarFactory(object):
    """Simple class to produce MrsVariables, incrementing the vid for
       each one."""

    def __init__(self, starting_vid=0):
        self.vid = starting_vid

    def new(self, sort, properties=None):
        self.vid += 1
        return MrsVariable(sort, self.vid-1, properties=properties)

sort_vid_re = re.compile(r'(\w*\D)(\d+)')
def sort_vid_split(vs):
    return sort_vid_re.match(vs).groups()
