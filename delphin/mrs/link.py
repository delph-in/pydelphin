
class Link(object):
    """DMRS-style Links are a way of representing arguments without
       variables. A Link encodes a start and end node, the argument
       name, and label information (e.g. label equality, qeq, etc)."""
    def __init__(self, start, end, argname=None, post=None):
        self.start    = int(start)
        self.end      = int(end)
        self.argname  = argname
        self.post     = post

    def __repr__(self):
        return 'Link({} -> {}, {}/{})'.format(self.start, self.end,
                                              self.argname, self.post)
