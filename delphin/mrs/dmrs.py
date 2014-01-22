from .var import VarFactory
from .ep import ElementaryPredication
from .hcons import qeq
from .xmrs import Xmrs

def get_dmrs_post(xmrs, nid1, argname, nid2):
    node2lbl = xmrs.eps[nid2].label
    if xmrs.eps[nid1].label == node2lbl:
        post = Dmrs.EQ
    elif xmrs.args.get(nid1,{}).get(argname) == node2lbl:
        post = Dmrs.HEQ
    else:
        hcon = xmrs.hcons_map.get(xmrs.args.get(nid1,{}).get(argname))
        if hcon is not None and hcon.rhandle == node2lbl:
            post = Dmrs.H
        else:
            post = Dmrs.NEQ
    return post

class Dmrs(Xmrs):
    EQ       = 'EQ'
    HEQ      = 'HEQ'
    NEQ      = 'NEQ'
    H        = 'H'
    CVARSORT = 'cvarsort'

    def __init__(self, ltop=None, index=None,
                 nodes=None, links=None,
                 lnk=None, surface=None, identifier=None):
        """Creating a DMRS object requires a bit of maintenance.
           Variables must be created for the labels and characteristic
           variables, and links must be converted to arguments."""
        self._links = links
        # now create necessary structure for making an Xmrs object. This is
        # essentially the same process as converting DMRS to RMRS
        vfac = VarFactory()
        # find common labels
        lbls = {}
        for l in links:
            if l.post == Dmrs.EQ:
                lbl = lbls.get(l.start) or lbls.get(l.end) or vfac.new('h')
                lbls[l.start] = lbls[l.end] = lbl
        # create any remaining uninstantiated labels
        for n in nodes:
            if n.nodeid not in lbls:
                lbls[n.nodeid] = vfac.new('h')
        # create characteristic variables (and bound variables)
        cvs = dict([(n.nodeid, vfac.new(n.properties.get(Dmrs.CVARSORT,'h'),
                                        n.properties or None)) for n in nodes])
        # convert links to args and hcons
        hcons = []
        args = []
        for l in links:
            if l.post == Dmrs.H or l.post == None:
                hole = vfac.new('h')
                hcons += [qeq(hole, lbls[l.end])]
                args += [(l.start, (l.argname, hole))]
            elif l.post == Dmrs.HEQ:
                args += [(l.start, (l.argname, lbls[l.end]))]
            else: # Dmrs.NEQ or Dmrs.EQ
                args += [(l.start, (l.argname, cvs[l.end]))]
        # "upgrade" nodes to EPs
        eps = [ElementaryPredication(n.pred, n.nodeid, lbls[n.nodeid],
                                     cvs[n.nodeid], args=None,
                                     lnk=n.lnk, surface=n.surface,
                                     base=n.base, carg=n.carg)
               for n in nodes]
        # TODO: icons not implemented yet
        icons = None
        # Finally, initialize the Xmrs using the converted structures
        Xmrs.__init__(self, ltop, index, args=args, eps=eps,
                      hcons=hcons, icons=icons,
                      lnk=lnk, surface=surface, identifier=identifier)
