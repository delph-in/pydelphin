from .hook import Hook
from .var import VarGenerator
from .ep import ElementaryPredication
from .arg import Argument
from .hcons import qeq
from .xmrs import Xmrs
from .config import (HANDLESORT, CVARG, CONSTARG, LTOP_NODEID, RSTR,
                     EQ_POST, HEQ_POST, H_POST, NIL_POST)


def Dmrs(nodes=None, links=None,
         lnk=None, surface=None, identifier=None,
         **kwargs):
    vgen = VarGenerator(starting_vid=0)
    labels = _make_labels(nodes, links, vgen)
    cvs = _make_cvs(nodes, vgen)
    hook = Hook(ltop=labels[LTOP_NODEID])  # no index for now
    # initialize args with ARG0 for characteristic variables
    args = {nid: [Argument(nid, CVARG, cv)] for nid, cv in cvs.items()}
    hcons = []
    for l in links:
        if l.start not in args:
            args[l.start] = []
        # FIXME: I don't have a clear answer about how LTOP links are
        # constructed, so I will assume that H_POST or NIL_POST
        # assumes a QEQ. Label equality would have been captured by
        # _make_labels() earlier.
        if l.start == LTOP_NODEID:
            if l.post == H_POST or l.post == NIL_POST:
                hcons += [qeq(labels[LTOP_NODEID], labels[l.end])]
        else:
            if l.argname is None:
                continue  # don't make an argument for bare EQ links
            if l.post == H_POST:
                hole = vgen.new(HANDLESORT)
                hcons += [qeq(hole, labels[l.end])]
                args[l.start].append(Argument(l.start, l.argname, hole))
                # if the arg is RSTR, it's a quantifier, so we can
                # find its characteristic variable now
                if l.argname.upper() == RSTR:
                    cvs[l.start] = cvs[l.end]
                    args[l.start].append(
                        Argument(l.start, CVARG, cvs[l.start])
                    )
            elif l.post == HEQ_POST:
                args[l.start].append(
                    Argument(l.start, l.argname, labels[l.end])
                )
            else:  # NEQ_POST or EQ_POST
                args[l.start].append(
                    Argument(l.start, l.argname, cvs[l.end])
                )
    eps = []
    for node in nodes:
        nid = node.nodeid
        if node.carg is not None:
            args[nid].append(Argument(nid, CONSTARG, node.carg))
        ep = ElementaryPredication.from_node(
            labels[nid], node, (args.get(nid) or None)
        )
        eps.append(ep)

    icons = None  # future feature
    return Xmrs.from_mrs(hook=hook, rels=eps,
                         hcons=hcons, icons=icons,
                         lnk=lnk, surface=surface, identifier=identifier)


def _make_labels(nodes, links, vgen):
    labels = {}
    labels[LTOP_NODEID] = vgen.new(HANDLESORT)  # reserve h0 for ltop
    for l in links:
        if l.post == EQ_POST:
            lbl = (labels.get(l.start) or
                   labels.get(l.end) or
                   vgen.new(HANDLESORT))
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
