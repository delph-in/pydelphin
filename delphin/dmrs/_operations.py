
"""
Operations on DMRS structures
"""

import warnings
from typing import Optional, cast

from delphin import dmrs, mrs, scope, variable
from delphin.sembase import ScopeMap

_HCMap = dict[str, mrs.HCons]
_IdMap = dict[str, int]


def from_mrs(
    m: mrs.MRS,
    representative_priority: Optional[scope.PredicationPriority] = None,
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
    # TODO: fix type annotation with scope.representatives overloads?
    reps = cast(
        dict[str, list[mrs.EP]],
        scope.representatives(m, priority=representative_priority)
    )
    # EP id to node id map; create now to keep ids consistent
    id_to_nid: _IdMap = {
        ep.id: i for i, ep in enumerate(m.rels, dmrs.FIRST_NODE_ID)
    }
    iv_to_nid: _IdMap = {
        ep.iv: id_to_nid[ep.id]
        for ep in m.rels
        if not ep.is_quantifier() and ep.iv is not None
    }

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
        identifier=m.identifier,
    )


def _mrs_get_top(
    top_var: Optional[str],
    hcmap: _HCMap,
    reps: ScopeMap,
    id_to_nid: _IdMap,
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
            warnings.warn(
                f'unusable TOP: {top_var}',
                dmrs.DMRSWarning,
                stacklevel=2,
            )
            top = None
    return top


def _mrs_to_nodes(m: mrs.MRS, id_to_nid: _IdMap) -> list[dmrs.Node]:
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
                    dmrs.DMRSWarning,
                    stacklevel=2,
                )
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
                ep.base,
            )
        )
    return nodes


def _mrs_to_links(
    m: mrs.MRS,
    hcmap: _HCMap,
    reps: dict[str, list[mrs.EP]],  # MRS-specific ScopeMap
    iv_to_nid: _IdMap,
    id_to_nid: _IdMap,
) -> list[dmrs.Link]:
    links = []
    # links from arguments
    for src_id, roleargs in m.arguments().items():
        start = id_to_nid[src_id]
        src_ep = cast(mrs.EP, m[src_id])
        for role, tgt in roleargs:
            # non-scopal arguments
            if tgt in iv_to_nid:
                tgt_ep = cast(mrs.EP, m[tgt])
                end = iv_to_nid[tgt]
                if src_ep.label == tgt_ep.label:
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
                            dmrs.DMRSWarning,
                            stacklevel=2,
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
    for _label, eps in reps.items():
        if len(eps) > 1:
            ep = eps[0]
            assert isinstance(ep, mrs.EP)
            end = id_to_nid[ep.id]
            for src_ep in eps[1:]:
                start = id_to_nid[src_ep.id]
                links.append(
                    dmrs.Link(start, end, dmrs.BARE_EQ_ROLE, dmrs.EQ_POST)
                )
    return links
