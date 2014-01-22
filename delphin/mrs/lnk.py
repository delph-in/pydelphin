
class Lnk(object):
    # lnk types
    # These types determine how a lnk on an EP or MRS are to be interpreted,
    # and thus determine the data type/structure of the lnk data
    CHARSPAN  = 'charspan'  # Character span; a pair of offsets
    CHARTSPAN = 'chartspan' # Chart vertex span: a pair of indices
    TOKENS    = 'tokens'    # Token numbers: a list of indices
    EDGE      = 'edge'      # An edge identifier: a number

    def __init__(self, data, type):
        self.type = type
        # simple type checking
        try:
            if type == self.CHARSPAN or type == self.CHARTSPAN:
                assert(len(data) == 2)
                self.data = (int(data[0]), int(data[1]))
            elif type == self.TOKENS:
                assert(len(data) > 0)
                self.data = tuple(int(t) for t in data)
            elif type == self.EDGE:
                self.data = int(data)
            else:
                raise ValueError('Invalid lnk type: {}'.format(type))
        except (AssertionError, TypeError):
            raise ValueError('Given data incompatible with given type: ' +\
                             '{}, {}'.format(data, type))
    def __str__(self):
        if self.type == self.CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == self.CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == self.EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == self.TOKENS:
            return '<{}>'.format(' '.join(self.data))

class LnkObject(object):
    """Lnks other than CHARSPAN are rarely used, so the presence of
       cfrom and cto are often assumed. In the case that they are
       undefined, this class (and those that inherit it) gives default
       values (-1)."""
    @property
    def cfrom(self):
        if self.lnk is not None and self.lnk.type == Lnk.CHARSPAN:
            return self.lnk.data[0]
        else:
            return -1

    @property
    def cto(self):
        if self.lnk is not None and self.lnk.type == Lnk.CHARSPAN:
            return self.lnk.data[1]
        else:
            return -1
