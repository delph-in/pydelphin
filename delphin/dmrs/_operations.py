
"""
Operations on DMRS structures
"""

from typing import Optional, Dict, List, Callable
import warnings

from delphin import variable
from delphin import scope
from delphin import mrs
from delphin import dmrs


_HCMap = Dict[str, mrs.HCons]
_IdMap = Dict[str, int]


def from_mrs(
    m: mrs.MRS, representative_priority: Callable = None
) -> dmrs.DMRS:
    """
    Create a DMRS by converting from MRS *m*.

    In order for MRS to DMRS conversion to work, the MRS must satisfy
    the intrinsic variable property (see
    :func:`delphin.mrs.has_intrinsic_variable_property`).

    Args:
        m: the input MRS
        representative_priority: a function for ranking candidate
            representative nodes; see :func:`scope.representatives`
    Returns:
        DMRS
    Raises:
        DMRSError when conversion fails.
    """
    hcmap: _HCMap = {hc.hi: hc for hc in m.hcons}
    reps = scope.representatives(m, priority=representative_priority)
    # EP id to node id map; create now to keep ids consistent
    id_to_nid: _IdMap = {ep.id: i
                         for i, ep in enumerate(m.rels, dmrs.FIRST_NODE_ID)}
    iv_to_nid: _IdMap = {ep.iv: id_to_nid[ep.id]
                         for ep in m.rels if not ep.is_quantifier()}

    top = _mrs_get_top(m.top, hcmap, reps, id_to_nid)
    # some bad MRSs have an INDEX that isn't the ARG0 of any EP, so
    # make sure it exists first
    index = None
    if m.index and m.index in iv_to_nid:
        index = iv_to_nid[m.index]
    nodes = _mrs_to_nodes(m, id_to_nid)
    links = _mrs_to_links(m, hcmap, reps, iv_to_nid, id_to_nid)

    return dmrs.DMRS(
        top=top,
        index=index,
        nodes=nodes,
        links=links,
        lnk=m.lnk,
        surface=m.surface,
        identifier=m.identifier)


def _mrs_get_top(
        top_var: Optional[str],
        hcmap: _HCMap,
        reps: scope.ScopeMap,
        id_to_nid: _IdMap
) -> Optional[int]:
    top: Optional[int]
    if top_var is None:
        top = None
    else:
        lbl = hcmap[top_var].lo if top_var in hcmap else top_var
        if lbl in reps:
            rep = reps[lbl][0]
            assert isinstance(rep, mrs.EP)
            top = id_to_nid[rep.id]
        else:
            warnings.warn(f'unusable TOP: {top_var}', dmrs.DMRSWarning)
            top = None
    return top


def _mrs_to_nodes(m: mrs.MRS, id_to_nid: _IdMap) -> List[dmrs.Node]:
    nodes = []
    for ep in m.rels:
        node_id = id_to_nid[ep.id]
        properties, type = None, None
        if not ep.is_quantifier():
            iv = ep.iv
            if iv is None:
                warnings.warn(
                    f'missing intrinsic variable for {ep!r}; morphosemantic '
                    'properties and node type information will be lost',
                    dmrs.DMRSWarning)
                properties = {}
                type = variable.UNSPECIFIC
            else:
                properties = m.properties(iv)
                type = variable.type(iv)
        nodes.append(
            dmrs.Node(node_id,
                      ep.predicate,
                      type,
                      properties,
                      ep.carg,
                      ep.lnk,
                      ep.surface,
                      ep.base))
    return nodes


def _mrs_to_links(
        m: mrs.MRS,
        hcmap: _HCMap,
        reps: scope.ScopeMap,
        iv_to_nid: _IdMap,
        id_to_nid: _IdMap
) -> List[dmrs.Link]:
    links = []
    # links from arguments
    for src, roleargs in m.arguments().items():
        start = id_to_nid[src]
        for role, tgt in roleargs:
            # non-scopal arguments
            if tgt in iv_to_nid:
                end = iv_to_nid[tgt]
                if m[src].label == m[tgt].label:
                    post = dmrs.EQ_POST
                else:
                    post = dmrs.NEQ_POST
            # scopal arguments
            else:
                if tgt in hcmap:
                    lbl = hcmap[tgt].lo
                    post = dmrs.H_POST
                    if lbl not in reps:
                        warnings.warn(
                            f'broken handle constraint: {hcmap[tgt]}',
                            dmrs.DMRSWarning
                        )
                else:
                    lbl = tgt
                    post = dmrs.HEQ_POST
                if lbl in reps and len(reps[lbl]) > 0:
                    ep = reps[lbl][0]
                    assert isinstance(ep, mrs.EP)
                    end = id_to_nid[ep.id]
                # BODY, dropped arguments, invalid, etc.
                else:
                    continue
            links.append(dmrs.Link(start, end, role, post))
    # MOD/EQ links for shared labels without argumentation
    for label, eps in reps.items():
        if len(eps) > 1:
            ep = eps[0]
            assert isinstance(ep, mrs.EP)
            end = id_to_nid[ep.id]
            for src in eps[1:]:
                start = id_to_nid[src.id]
                links.append(
                    dmrs.Link(start, end, dmrs.BARE_EQ_ROLE, dmrs.EQ_POST))
    return links
