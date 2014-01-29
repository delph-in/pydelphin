from .config import (CHARSPAN, CHARTSPAN, TOKENS, EDGE)

class Lnk(object):
    """
    Lnk objects link predicates to the surface form in one of several
    ways, the most common of which being the character span of the
    original string.
    """
    def __init__(self, data, type):
        if type not in (CHARSPAN, CHARTSPAN, TOKENS, EDGE):
            raise ValueError('Invalid lnk type: {}'.format(type))
        self.type = type
        # simple type checking
        try:
            if type == CHARSPAN or type == CHARTSPAN:
                assert(len(data) == 2)
                self.data = (int(data[0]), int(data[1]))
            elif type == TOKENS:
                assert(len(data) > 0)
                self.data = tuple(int(t) for t in data)
            elif type == EDGE:
                self.data = int(data)
            else:
                raise ValueError('Invalid lnk type: {}'.format(type))
        except (AssertionError, TypeError):
            raise ValueError('Given data incompatible with given type: ' +\
                             '{}, {}'.format(data, type))
    def __str__(self):
        if self.type == CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == TOKENS:
            return '<{}>'.format(' '.join(self.data))

class LnkObject(object):
    """Lnks other than CHARSPAN are rarely used, so the presence of
       cfrom and cto are often assumed. In the case that they are
       undefined, this class (and those that inherit it) gives default
       values (-1)."""
    @property
    def cfrom(self):
        if self.lnk is not None and self.lnk.type == CHARSPAN:
            return self.lnk.data[0]
        else:
            return -1

    @property
    def cto(self):
        if self.lnk is not None and self.lnk.type == CHARSPAN:
            return self.lnk.data[1]
        else:
            return -1
