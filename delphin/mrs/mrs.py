import logging
from .lnk import Lnk
from .hook import Hook
from .var import MrsVariable
from .xmrs import Xmrs
from .config import (FIRST_NODEID, ANCHOR_SORT)


def Mrs(ltop=None, index=None, rels=None, hcons=None, icons=None,
        lnk=None, surface=None, identifier=None):
    """
    Construct an |Xmrs| using MRS components.

    Formally, Minimal Recursion Semantics (MRS) have a top handle, a
    bag of |ElementaryPredications|, and a bag of |HandleConstraints|.
    All |Arguments|, including intrinsic arguments and constant
    arguments, are expected to be contained by the |EPs|.

    Args:
        ltop: an |MrsVariable| for the top handle
        index: an |MrsVariable| for the index
        rels: a list of |ElementaryPredications|
        hcons: a list of |HandleConstraints|
        icons: a list of IndividualConstraints (planned feature)
        lnk: the |Lnk| object associating the MRS to the surface form
        surface: the surface string
        identifier: a discourse-utterance id
    Returns:
        an |Xmrs| object

    Example:

    >>> ltop = MrsVariable(vid=0, sort='h')
    >>> rain_label = MrsVariable(vid=1, sort='h')
    >>> index = MrsVariable(vid=2, sort='e')
    >>> m = Mrs(
    >>>     ltop=ltop, index=index,
    >>>     rels=[ElementaryPredication(
    >>>         Pred.stringpred('_rain_v_1_rel'),
    >>>         label=rain_label,
    >>>         anchor=MrsVariable(vid=10000, sort='h'),
    >>>         args=[Argument(10000, 'ARG0', index)]
    >>>         )
    >>>     ],
    >>>     hcons=[HandleConstraint(ltop, 'qeq', rain_label)]
    >>> )
    """
    return Xmrs.from_mrs(Hook(ltop=ltop, index=index), rels, hcons, icons,
                         lnk, surface, identifier)
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
        # the args' nodeids will be set by the above
        #for arg in ep.args:
        #    arg.anchor = anchor

    # maybe validation can do further finishing, like adding CVs or
    # setting argument types
    validate(ltop, index, rels, hcons, icons, lnk, surface, identifier)

    # construct Xmrs structures
    hook = Hook(ltop=ltop, index=index)
    # if there's no MRS lnk, get the min cfrom and max cto (if not using
    # charspan lnks, it will get -1 and -1 anyway)
    if lnk is None:
        lnk = Lnk.charspan(min([ep.cfrom for ep in rels] or [-1]),
                           max([ep.cto for ep in rels] or [-1]))
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
