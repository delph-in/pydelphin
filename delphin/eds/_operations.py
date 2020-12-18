
"""
Operations on EDS
"""

import warnings
from itertools import count

from delphin import variable
from delphin import scope
from delphin import eds
from delphin import util


def from_mrs(m, predicate_modifiers=True, unique_ids=True,
             representative_priority=None):
    """
    Create an EDS by converting from MRS *m*.

    In order for MRS to EDS conversion to work, the MRS must satisfy
    the intrinsic variable property (see
    :func:`delphin.mrs.has_intrinsic_variable_property`).

    Args:
        m: the input MRS
        predicate_modifiers: if `True`, include predicate-modifier
            edges; if `False`, only include basic dependencies; if a
            callable, then call on the converted EDS before creating
            unique ids (if `unique_ids=True`)
        unique_ids: if `True`, recompute node identifiers to be unique
            by the LKB's method; note that ids from *m* should already
            be unique by PyDelphin's method
        representative_priority: a function for ranking candidate
            representative nodes; see :func:`scope.representatives`
    Returns:
        EDS
    Raises:
        EDSError: when conversion fails.
    """
    # EP id to node id map; create now to keep ids consistent
    hcmap = {hc.hi: hc for hc in m.hcons}
    reps = scope.representatives(m, priority=representative_priority)
    ivmap = {p.iv: (p, q)
             for p, q in m.quantification_pairs()
             if p is not None}

    top = _mrs_get_top(m.top, hcmap, reps, m.index, ivmap)
    deps = _mrs_args_to_basic_deps(m, hcmap, ivmap, reps)
    nodes = _mrs_to_nodes(m, deps)

    e = eds.EDS(
        top=top,
        nodes=nodes,
        lnk=m.lnk,
        surface=m.surface,
        identifier=m.identifier)

    if predicate_modifiers is True:
        predicate_modifiers = find_predicate_modifiers
    if predicate_modifiers:
        addl_deps = predicate_modifiers(e, m, representatives=reps)
        for id, node_deps in addl_deps.items():
            e[id].edges.update(node_deps)

    if unique_ids:
        make_ids_unique(e, m)

    return e


def _mrs_get_top(top, hcmap, reps, index, ivmap):
    if top in hcmap and hcmap[top].lo in reps:
        lbl = hcmap[top].lo
        top = reps[lbl][0].id
    else:
        if top in hcmap:
            warnings.warn(
                f'broken handle constraint: {hcmap[top]}',
                eds.EDSWarning
            )
        if top in reps:
            top = reps[top][0].id
        elif index in ivmap and ivmap[index][0].label in reps:
            lbl = ivmap[index][0].label
            top = reps[lbl][0].id
        else:
            warnings.warn('unable to find a suitable TOP', eds.EDSWarning)
            top = None
    return top


def _mrs_args_to_basic_deps(m, hcmap, ivmap, reps):
    edges = {}
    for src, roleargs in m.arguments().items():
        if src in ivmap:
            p, q = ivmap[src]
            # non-quantifier EPs
            edges[src] = {}
            for role, tgt in roleargs:
                # qeq
                if tgt in hcmap:
                    lbl = hcmap[tgt].lo
                    if lbl in reps:
                        tgt = reps[lbl][0].id
                    else:
                        warnings.warn(
                            f'broken handle constraint: {hcmap[tgt]}',
                            eds.EDSWarning
                        )
                        continue
                # label arg
                elif tgt in reps:
                    tgt = reps[tgt][0].id
                # regular arg
                elif tgt in ivmap:
                    tgt = ivmap[tgt][0].id
                # other (e.g., BODY, dropped arguments, etc.)
                else:
                    continue
                edges[src][role] = tgt
            # add BV if the EP has a quantifier
            if q is not None:
                edges[q.id] = {eds.BOUND_VARIABLE_ROLE: src}

    return edges


def _mrs_to_nodes(m, edges):
    nodes = []
    for ep in m.rels:
        properties, type = None, None
        if not ep.is_quantifier():
            iv = ep.iv
            properties = m.properties(iv)
            type = variable.type(iv)
        nodes.append(
            eds.Node(ep.id,
                     ep.predicate,
                     type,
                     edges.get(ep.id, {}),
                     properties,
                     ep.carg,
                     ep.lnk,
                     ep.surface,
                     ep.base))
    return nodes


def find_predicate_modifiers(e, m, representatives=None):
    """
    Return an argument structure mapping for predicate-modifier edges.

    In EDS, predicate modifiers are edges that describe a relation
    between predications in the original MRS that is not evident on
    the regular and scopal arguments. In practice these are EPs that
    share a scope but do not select any other EPs within their scope,
    such as when quantifiers are modified ("nearly every...") or with
    relative clauses ("the chef whose soup spilled..."). These are
    almost the same as the MOD/EQ links of DMRS, except that predicate
    modifiers have more restrictions on their usage, mainly due to
    their using a standard role (`ARG1`) instead of an
    idiosyncratic one.

    Generally users won't call this function directly, but by calling
    :func:`from_mrs` with `predicate_modifiers=True`, but it is
    visible here in case users want to inspect its results separately
    from MRS-to-EDS conversion. Note that when calling it separately,
    *e* should use the same predication ids as *m* (by calling
    :func:`from_mrs` with `unique_ids=False`). Also, users may define
    their own function with the same signature and return type and use
    it in place of this one. See :func:`from_mrs` for details.

    Args:
        e: the EDS converted from *m* as by calling :func:`from_mrs`
            with `predicate_modifiers=False` and `unique_ids=False`,
            used to determine if parts of the graph are connected
        m: the source MRS
        representatives: the scope representatives; this argument is
            mainly to prevent :func:`delphin.scope.representatives`
            from being called twice on *m*
    Returns:
        A dictionary mapping source node identifiers to
        role-to-argument dictionaries of any additional
        predicate-modifier edges.
    Examples:
        >>> e = eds.from_mrs(m, predicate_modifiers=False)
        >>> print(eds.find_predicate_modifiers(e.argument_structure(), m)
        {'e5': {'ARG1': '_1'}}
    """
    if representatives is None:
        representatives = scope.representatives(m)
    role = eds.PREDICATE_MODIFIER_ROLE

    # find connected components so predicate modifiers only connect
    # separate components
    ids = {ep.id for ep in m.rels}
    edges = []
    for node in e.nodes:
        for _, tgt in node.edges.items():
            edges.append((node.id, tgt))
    components = util._connected_components(ids, edges)

    ccmap = {}
    for i, component in enumerate(components):
        for id in component:
            ccmap[id] = i

    addl = {}
    if len(components) > 1:
        for label, eps in representatives.items():
            if len(eps) > 1:
                first = eps[0]
                joined = set([ccmap[first.id]])
                for other in eps[1:]:
                    occ = ccmap[other.id]
                    type = variable.type(other.args.get(role, 'u0'))
                    needs_edge = occ not in joined
                    edge_available = type.lower() == 'u'
                    if needs_edge and edge_available:
                        addl.setdefault(other.id, {})[role] = first.id
                        joined.add(occ)
    return addl


def make_ids_unique(e, m):
    """
    Recompute the node identifiers in EDS *e* to be unique.

    MRS objects used in conversion to EDS already have unique
    predication ids, but they are created according to PyDelphin's
    method rather than the LKB's method, namely with regard to
    quantifiers and MRSs that do not have the intrinsic variable
    property. This function recomputes unique EDS node identifiers by
    the LKB's method.

    .. note::
        This function works in-place on *e* and returns nothing.

    Args:
        e: an EDS converted from MRS *m*, as from :func:`from_mrs`
            with `unique_ids=False`
        m: the MRS from which *e* was converted
    """
    # deps can be used to single out ep from set sharing ARG0s
    new_ids = (f'_{i}' for i in count(start=1))
    nids = {}
    used = {}
    # initially only make new ids for quantifiers and those with no IV
    for ep in m.rels:
        nid = ep.iv
        if nid is None or ep.is_quantifier():
            nid = next(new_ids)
        nids[ep.id] = nid
        used.setdefault(nid, set()).add(ep.id)
    # for ill-formed MRSs, more than one non-quantifier EP may have
    # the same IV. Select a winner like selecting a scope
    # representatives: the one not taking others in its group as an
    # argument.
    deps = {node.id: node.edges.items() for node in e.nodes}
    for nid, ep_ids in used.items():
        if len(ep_ids) > 1:
            ep_ids = sorted(
                ep_ids,
                key=lambda n: any(d in ep_ids for _, d in deps.get(n, []))
            )
            for nid in ep_ids[1:]:
                nids[nid] = next(new_ids)

    # now use the unique ID mapping for reassignment
    if e.top is not None:
        e.top = nids[e.top]
    for node in e.nodes:
        node.id = nids[node.id]
        edges = {role: nids[arg] for role, arg in node.edges.items()}
        node.edges = edges
