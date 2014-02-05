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
        self.data = data

    @classmethod
    def charspan(cls, start, end):
        return cls((int(start), int(end)), CHARSPAN)

    @classmethod
    def chartspan(cls, start, end):
        return cls((int(start), int(end)), CHARTSPAN)

    @classmethod
    def tokens(cls, tokens):
        return cls(tuple(map(int, tokens)), TOKENS)

    @classmethod
    def edge(cls, edge):
        return cls(int(edge), EDGE)

    def __str__(self):
        if self.type == CHARSPAN:
            return '<{}:{}>'.format(self.data[0], self.data[1])
        elif self.type == CHARTSPAN:
            return '<{}#{}>'.format(self.data[0], self.data[2])
        elif self.type == EDGE:
            return '<@{}>'.format(self.data)
        elif self.type == TOKENS:
            return '<{}>'.format(' '.join(self.data))

    def __eq__(self, other):
        return self.type == other.type and self.data == other.data

class LnkMixin(object):
    """
    Lnks other than CHARSPAN are rarely used, so the presence of cfrom
    and cto are often assumed. In the case that they are undefined,
    this class (and those that inherit it) gives default values (-1).
    """
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
