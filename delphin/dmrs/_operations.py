
"""
Operations on DMRS structures
"""

from delphin import variable
from delphin import scope
from delphin import dmrs


def from_mrs(m):
    """
    Create a DMRS by converting from MRS *m*.

    In order for MRS to DMRS conversion to work, the MRS must satisfy
    the intrinsic variable property (see
    :func:`delphin.mrs.has_intrinsic_variable_property`).

    Args:
        m: the input MRS
    Returns:
        DMRS
    Raises:
        DMRSError when conversion fails.
    """
    # EP id to node id map; create now to keep ids consistent
    id_to_nid = {ep.id: i for i, ep in enumerate(m.rels, dmrs.FIRST_NODE_ID)}
    nodes, iv_to_nid = _mrs_to_nodes(m, id_to_nid)
    links, top = _mrs_to_links(m, id_to_nid, iv_to_nid)
    index = iv_to_nid[m.index] if m.index else None
    return dmrs.DMRS(
        top=top,
        index=index,
        nodes=nodes,
        links=links,
        lnk=m.lnk,
        surface=m.surface,
        identifier=m.identifier)


def _mrs_to_nodes(m, id_to_nid):
    nodes = []
    iv_to_nid = {}
    for ep in m.rels:
        node_id = id_to_nid[ep.id]
        iv = ep.iv
        nodes.append(
            dmrs.Node(node_id,
                      ep.predicate,
                      variable.type(iv),
                      m.properties(iv),
                      ep.carg,
                      ep.lnk,
                      ep.surface,
                      ep.base))
        if not ep.is_quantifier():
            iv_to_nid[iv] = node_id
    return nodes, iv_to_nid


def _mrs_to_links(m, id_to_nid, iv_to_nid):
    links = []
    hcmap = {hc.hi: hc for hc in m.hcons}
    reps = scope.representatives(m)

    top = None
    if m.top in hcmap:
        lbl = hcmap[m.top].lo
        rep = reps[lbl][0]
        top = id_to_nid[rep]
    elif m.top in reps:
        rep = reps[top][0]
        top = id_to_nid[rep]

    for src, roleargs in m.arguments().items():
        start = id_to_nid[src]
        for role, tgt in roleargs.items():

            if tgt in iv_to_nid:
                if m[src].label == m[tgt].label:
                    post = dmrs.EQ_POST
                else:
                    post = dmrs.NEQ_POST

            elif tgt in reps and len(reps[tgt]) > 0:
                tgt = reps[tgt][0]
                post = dmrs.HEQ_POST

            elif tgt in hcmap:
                lo = hcmap[tgt].lo
                tgt = reps[lo][0]
                post = dmrs.H_POST

            else:
                continue  # e.g., BODY, dropped arguments, etc.

            end = iv_to_nid[tgt]
            links.append(dmrs.Link(start, end, role, post))

    return links, top
