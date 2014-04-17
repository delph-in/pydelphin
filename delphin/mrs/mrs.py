import logging
from .lnk import Lnk
from .hook import Hook
from .var import MrsVariable
from .xmrs import Xmrs
from .config import (FIRST_NODEID, ANCHOR_SORT)


def Mrs(ltop=None, index=None, rels=None, hcons=None, icons=None,
        lnk=None, surface=None, identifier=None):
    """Minimal Recursion Semantics contains a top handle, a bag
       of ElementaryPredications, and a bag of handle constraints."""
    # default values or run generators
    rels = list(rels or [])
    hcons = list(hcons or [])
    icons = list(icons or [])

    # Xmrs requires that EPs and Arguments have anchors, so add those
    # if necessary
    for i, ep in enumerate(rels):
        # setting anchor for model consistency, but it may be faster
        # to just set the nodeid directly
        anchor = MrsVariable(vid=FIRST_NODEID + i, sort=ANCHOR_SORT)
        if ep.anchor is None:
            ep.anchor = anchor
        for arg in ep.args:
            arg.anchor = anchor

    # maybe validation can do further finishing, like adding CVs or
    # setting argument types
    validate(ltop, index, rels, hcons, icons, lnk, surface, identifier)

    # construct Xmrs structures
    hook = Hook(ltop=ltop, index=index)
    # if there's no MRS lnk, get the min cfrom and max cto (if not using
    # charspan lnks, it will get -1 and -1 anyway)
    if lnk is None:
        lnk = Lnk.charspan(min(ep.cfrom for ep in rels),
                           max(ep.cto for ep in rels))
    return Xmrs(hook=hook, eps=rels,
                hcons=hcons, icons=icons,
                lnk=lnk, surface=surface, identifier=identifier)


def validate(ltop, index, rels, hcons, icons, lnk, surface, identifier):
    # TODO: check if there are labels?
    lbls = set(ep.label for ep in rels)
    hcmap = {hc.lo: hc for hc in hcons}
    for ep in rels:
        if ep.cv is None:
            logging.warning('The EP for {} is missing a characteristic '
                            'variable.'.format(ep.pred))
        for arg in ep.args:
            if arg.value in hcmap and hcmap[arg.value].lo not in lbls:
                logging.warning('The lo variable ({0.lo}) of HCONS {0}'
                                'is not the label of any EP in the MRS.'
                                .format(hcmap[arg.value]))
