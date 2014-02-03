from .config import (QEQ, LHEQ, OUTSCOPES)

class HandleConstraint(object):
    """A relation between two handles."""

    def __init__(self, hi, relation, lo):
        self.hi = hi
        self.relation = relation
        self.lo = lo

    @classmethod
    def qeq(cls, hi, lo):
        return cls(hi, QEQ, lo)

    @classmethod
    def lheq(cls, hi, lo):
        return cls(hi, LHEQ, lo)

    @classmethod
    def outscopes(cls, hi, lo):
        return cls(hi, OUTSCOPES, lo)

    def __eq__(self, other):
        return self.hi == other.hi and\
               self.relation == other.relation and\
               self.lo == other.lo

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return 'HandleConstraint({})'.format(
               ' '.join([str(self.hi), self.relation, str(self.lo)]))

    def __str__(self):
        return self.__repr__()

# note: with the classmethods defined above, this becomes deprecated
def qeq(hi, lo):
    return HandleConstraint(hi, QEQ, lo)
