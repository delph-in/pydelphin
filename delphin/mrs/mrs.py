import logging
from collections import OrderedDict
from .hook import Hook
from .var import MrsVariable
from .node import Node
from .xmrs import Xmrs
from .config import (FIRST_NODEID, CVARSORT, ANCHOR_SORT)

def Mrs(ltop=None, index=None, rels=None, hcons=None, icons=None,
        lnk=None, surface=None, identifier=None):
    """Minimal Recursion Semantics contains a top handle, a bag
       of ElementaryPredications, and a bag of handle constraints."""
    # default values
    if rels is None: rels = []
    if hcons is None: hcons = []
    if icons is None: pass # do nothing for now

    # Xmrs requires that EPs and Arguments have anchors, so add those
    # if necessary
    for i, ep in enumerate(rels):
        # setting anchor for model consistency, but it may be faster
        # to just set the nodeid directly
        if ep.anchor is None:
            ep.anchor = MrsVariable(vid=FIRST_NODEID + i, sort=ANCHOR_SORT)
        for arg in ep.args:
            arg.anchor = ep.anchor

    # maybe validation can do further finishing, like adding CVs or
    # setting argument types
    validate(ltop, index, rels, hcons, icons, lnk, surface, identifier)

    # construct Xmrs structures
    hook = Hook(ltop=ltop, index=index)
    nodes = []
    args = []
    cvs = []
    labels = []
    for ep in rels:
        labels.append((ep.nodeid, ep.label))
        if ep.cv:
            sortinfo = OrderedDict([(CVARSORT, ep.cv.sort)] +\
                                   list(ep.properties.items()))
            cvs.append((ep.nodeid, ep.cv))
        else:
            sortinfo = None
        nodes.append(Node(ep.nodeid, ep.pred, sortinfo=sortinfo,
            lnk=ep.lnk, surface=ep.surface, base=ep.base, carg=ep.carg))
        args.extend(ep.args)
    return Xmrs(hook=hook, nodes=nodes, args=args,
                hcons=hcons, icons=icons,
                cvs=cvs, labels=labels,
                lnk=lnk, surface=surface, identifier=identifier)

def validate(ltop, index, rels, hcons, icons, lnk, surface, identifier):
    #TODO: check if there are labels?
    lbls = set(ep.label for ep in rels)
    hcmap = {hc.lo:hc for hc in hcons}
    for ep in rels:
        if ep.cv is None:
            logging.warning('The EP for {} is missing a characteristic '
                            'variable.'.format(ep.pred))
        for arg in ep.args:
            if arg.value in hcmap and hcmap[arg.value].lo not in lbls:
                logging.warning('The lo variable ({0.lo}) of HCONS {0}'
                                'is not the label of any EP in the MRS.'
                                .format(hcmap[arg.value]))

