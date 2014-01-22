
class HandleConstraint(object):
    """A relation between two handles."""

    QEQ       = 'qeq'
    LHEQ      = 'lheq'
    OUTSCOPES = 'outscopes'

    def __init__(self, lhandle, relation, rhandle):
        self.lhandle = lhandle
        self.relation = relation
        self.rhandle = rhandle

    def __eq__(self, other):
        return self.lhandle == other.lhandle and\
               self.relation == other.relation and\
               self.rhandle == other.rhandle

    def __hash__(self):
        return hash(repr(self))

    def __repr__(self):
        return 'HandleConstraint({})'.format(
               ' '.join([str(self.lhandle), self.relation, str(self.rhandle)]))

    def __str__(self):
        return self.__repr__()

def qeq(hi, lo):
    return HandleConstraint(hi, HandleConstraint.QEQ, lo)
