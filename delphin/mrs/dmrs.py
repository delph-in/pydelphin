from collections import defaultdict
from .hook import Hook
from .var import VarGenerator
from .arg import Argument
from .ep import ElementaryPredication
from .hcons import qeq
from .xmrs import Xmrs
from .config import (HANDLESORT, CVARSORT, CVARG, LTOP_NODEID, RSTR,
                     EQ_POST, HEQ_POST, NEQ_POST, H_POST, NIL_POST)

def get_dmrs_post(xmrs, nid1, argname, nid2):
    node2lbl = xmrs.eps[nid2].label
    if xmrs.eps[nid1].label == node2lbl:
        post = EQ_POST
    elif xmrs._nid_to_argmap.get(nid1,{}).get(argname).value == node2lbl:
        post = HEQ_POST
    else:
        hcon = xmrs.hcons_map.get(xmrs._nid_to_argmap.get(nid1,{}).get(argname).value)
        if hcon is not None and hcon.lo == node2lbl:
            post = H_POST
        else:
            post = NEQ_POST
    return post

def Dmrs(nodes=None, links=None,
         lnk=None, surface=None, identifier=None,
         **kwargs):
    vgen = VarGenerator(starting_vid=0)
    labels = _make_labels(nodes, links, vgen)
    hook = Hook(ltop=labels[LTOP_NODEID]) # no index for now
    cvs = _make_cvs(nodes, vgen)
    # initialize args with ARG0 for characteristic variables
    args = [Argument(nid, CVARG, cv) for nid, cv in cvs.items()]
    hcons = []
    for l in links:
        #FIXME: I don't have a clear answer about how LTOP links are
        # constructed, so I will assume that H_POST or NIL_POST
        # assumes a QEQ. Label equality would have been captured by
        # _make_labels() earlier.
        if l.start == LTOP_NODEID:
            if l.post == H_POST or l.post == NIL_POST:
                hcons += [qeq(labels[LTOP_NODEID], labels[l.end])]
        else:
            if l.post == H_POST:
                hole = vgen.new(HANDLESORT)
                hcons += [qeq(hole, labels[l.end])]
                args += [Argument(l.start, l.argname, hole)]
                # if the arg is RSTR, it's a quantifier, so we can
                # find its characteristic variable now
                if l.argname.upper() == RSTR:
                    cvs[l.start] = cvs[l.end]
                    args += [Argument(l.start, CVARG, cvs[l.start])]
            elif l.post == HEQ_POST:
                args += [Argument(l.start, l.argname, labels[l.end])]
            else: # NEQ_POST or EQ_POST
                args += [Argument(l.start, l.argname, cvs[l.end])]

    icons = None # future feature
    return Xmrs(hook=hook, nodes=nodes, args=args,
                hcons=hcons, icons=icons,
                cvs=cvs.items(), labels=labels.items(),
                lnk=lnk, surface=surface, identifier=identifier)

def _make_labels(nodes, links, vgen):
    labels = {}
    labels[LTOP_NODEID] = vgen.new(HANDLESORT) # reserve h0 for ltop
    for l in links:
        if l.post == EQ_POST:
            lbl = labels.get(l.start) or labels.get(l.end) or\
                    vgen.new(HANDLESORT)
            labels[l.start] = labels[l.end] = lbl
    # create any remaining uninstantiated labels
    for n in nodes:
        if n.nodeid not in labels:
            labels[n.nodeid] = vgen.new(HANDLESORT)
    return labels

def _make_cvs(nodes, vgen):
    cvs = {}
    for node in nodes:
        # quantifiers share their CV with the quantifiee. It will be
        # selected later during argument construction
        if not node.is_quantifier():
            cvs[node.nodeid] = vgen.new(node.cvarsort,
                                        node.properties or None)
    return cvs