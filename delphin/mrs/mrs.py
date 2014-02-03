import logging
from collections import defaultdict
from .hook import Hook
from .var import MrsVariable
from .xmrs import Xmrs
from .config import (FIRST_NODEID)

class Mrs(Xmrs):
    """Minimal Recursion Semantics class containing a top handle, a bag
       of ElementaryPredications, and a bag of handle constraints."""

    TOP_HANDLE = 'ltop'
    MAIN_EVENT_VAR = 'index'

    def __init__(self, ltop=None, index=None,
                 rels=None, hcons=None, icons=None,
                 lnk=None, surface=None, identifier=None):
        if rels is None: rels = []
        if hcons is None: hcons = []
        hook = Hook(ltop=ltop, index=index)
        for i, ep in enumerate(rels):
            ep.nodeid = FIRST_NODEID + i
            for arg in ep.args:
                arg.nodeid = ep.nodeid
        args = [arg for ep in rels for arg in ep.args]
        Xmrs.__init__(self, hook, args=args, eps=rels,
                      hcons=hcons, icons=icons,
                      lnk=lnk, surface=surface, identifier=identifier)
        # store these so the rels() method can find them
        self._rels = rels
