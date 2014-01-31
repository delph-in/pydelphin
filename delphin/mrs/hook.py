
class Hook(object):
    """Container class for ltop, index, and xarg."""
    def __init__(self, ltop=None, index=None, xarg=None):
        """
        :param ltop: vid of the label of the local-top predicates
            (usually same as index, but may differ; e.g. "kim
            sleeps maybe", sleeps is the index, but maybe is
            the ltop (or is QEQed by the LTOP))
        :param index: nodeid of most salient predicate (i.e. semantic head)
        """
        self.ltop   = ltop
        self.index  = index
        self.xarg   = xarg
