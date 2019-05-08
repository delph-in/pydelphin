
"""
Operations on MRS structures
"""

from typing import Iterable

from delphin import variable
from delphin import predicate
from delphin import sembase
from delphin import mrs
from delphin import util


def is_connected(m: mrs.MRS) -> bool:
    """
    Return `True` if *m* is a fully-connected MRS.

    A connected MRS is one where, when viewed as a graph, all EPs are
    connected to each other via regular (non-scopal) arguments, scopal
    arguments (including qeqs), or label equalities.
    """
    ids = {ep.id for ep in m.rels}
    g = {id: set() for id in ids}
    # first establish links from labels and intrinsic variables to EPs
    for ep in m.rels:
        id, lbl, iv = ep.id, ep.label, ep.iv
        g[id].update((lbl, iv))
        g.setdefault(lbl, set()).add(id)
        if iv:
            g.setdefault(iv, set()).add(id)
    # arguments may link EPs with IVs or labels (or qeq) as targets
    hcmap = {hc.hi: hc.lo for hc in m.hcons}
    for id, roleargs in m.arguments().items():
        for role, value in roleargs.items():
            value = hcmap.get(value, value)  # resolve qeq if any
            if value in g:
                g[id].add(value)
                g[value].add(iv)
    return ids.issubset(util._bfs(g))


def has_intrinsic_variable_property(m: mrs.MRS) -> bool:
    """
    Return `True` if *m* satisfies the intrinsic variable property.

    An MRS has the intrinsic variable property when:

    * Every non-quantifier EP has an argument for the intrinsic role
      (i.e., specifies an `ARG0`)

    * Every intrinsic variable is unique to a non-quantifier EP

    Note that for quantifier EPs, `ARG0` is overloaded to mean "bound
    variable". Each quantifier should have an `ARG0` that is the
    intrinsic variable of exactly one non-quantifier EP, but this
    function does not check for that.
    """
    seen = set()
    for ep in m.rels:
        if not ep.is_quantifier():
            iv = ep.iv
            if iv is None:
                return False  # EP does not have an intrinsic variable
            elif iv in seen:  # intrinsic variable is not unique
                return False
            seen.add(iv)
    return True


def is_well_formed(m: mrs.MRS) -> bool:
    return (is_connected(m)
            and has_intrinsic_variable_property(m))


def is_isomorphic(m1: mrs.MRS,
                  m2: mrs.MRS,
                  properties: bool = True) -> bool:
    """
    Return `True` if *m1* and *m2* are isomorphic MRSs.

    Isomorphicity compares the predicates of a semantic structure, the
    morphosemantic properties of their predications (if
    `properties=True`), constant arguments, and the argument structure
    between predications. Non-semantic properties like identifiers and
    surface alignments are ignored.

    Args:
        m1: the left MRS to compare
        m2: the right MRS to compare
        properties: if `True`, ensure variable properties are
            equal for mapped predications
    """
    # loading NetworkX is slow; only do this when is_isomorphic is called
    import networkx as nx

    m1dg = _make_mrs_digraph(m1, nx.DiGraph(), properties)
    m2dg = _make_mrs_digraph(m2, nx.DiGraph(), properties)

    def nem(m1d, m2d):  # node-edge-match
        return m1d.get('sig') == m2d.get('sig')

    return nx.is_isomorphic(m1dg, m2dg, node_match=nem, edge_match=nem)


def _make_mrs_digraph(x, dg, properties):
    # scope labels (may be targets of arguments or hcons)
    for label, ids in x.scopes().items():
        dg.add_edges_from((label, x[id].iv, {'sig': 'eq-scope'})
                          for id in ids)
    # predicate-argument structure
    for ep in x.rels:
        iv, pred, args = ep.iv, ep.predicate, ep.args
        if ep.is_quantifier():
            iv += '(bound)'  # make sure node id is unique
        s = predicate.normalize(pred)
        if mrs.CONSTANT_ROLE in args:
            s += '({})'.format(args[mrs.CONSTANT_ROLE])
        if properties and not ep.is_quantifier():
            props = x.variables[iv]
            s += '{{{}}}'.format('|'.join(
                '{}={}'.format(prop.upper(), props[prop].lower())
                for prop in sorted(props, key=sembase.property_priority)))
        dg.add_node(iv, sig=s)
        dg.add_edges_from((iv, args[role], {'sig': role})
                          for role in sorted(args, key=sembase.role_priority)
                          if role != mrs.CONSTANT_ROLE)
    # hcons
    dg.add_edges_from((hc.hi, hc.lo, {'sig': hc.relation})
                      for hc in x.hcons)
    # icons
    dg.add_edges_from((ic.left, ic.right, {'sig': ic.relation})
                      for ic in x.icons)
    return dg


def compare_bags(testbag: Iterable[mrs.MRS],
                 goldbag: Iterable[mrs.MRS],
                 properties: bool = True,
                 count_only: bool = True):
    """
    Compare two bags of MRS objects, returning a triple of
    (unique-in-test, shared, unique-in-gold).

    Args:
        testbag: An iterable of MRS objects to test
        goldbag: An iterable of MRS objects to compare against
        properties: if `True`, ensure variable properties are
            equal for mapped predications
        count_only: If `True`, the returned triple will only have the
            counts of each; if `False`, a list of MRS objects will be
            returned for each (using the ones from *testbag* for the
            shared set)
    Returns:
        A triple of (unique-in-test, shared, unique-in-gold), where
        each of the three items is an integer count if the
        *count_only* parameter is `True`, or a list of MRS objects
        otherwise.
    """
    gold_remaining = list(goldbag)
    test_unique = []
    shared = []
    for test in testbag:
        gold_match = None
        for gold in gold_remaining:
            if is_isomorphic(test, gold, properties=properties):
                gold_match = gold
                break
        if gold_match is not None:
            gold_remaining.remove(gold_match)
            shared.append(test)
        else:
            test_unique.append(test)
    if count_only:
        return (len(test_unique), len(shared), len(gold_remaining))
    else:
        return (test_unique, shared, gold_remaining)


def from_dmrs(d):
    """
    Create an MRS by converting from DMRS *d*.

    Args:
        d: the input DMRS
    Returns:
        MRS
    Raises:
        MRSError when conversion fails.
    """
    qeq = mrs.HCons.qeq
    vfac = variable.VariableFactory(starting_vid=0)

    top = vfac.new(variable.HANDLE)
    index = None
    id_to_lbl, id_to_iv, id_to_link = _dmrs_build_maps(d, vfac)

    hcons = [qeq(top, id_to_lbl[d.top])]
    icons = None

    rels = []
    for node in d.nodes:
        label = id_to_lbl[node.id]
        args = {mrs.INTRINSIC_ROLE: id_to_iv[node.id]}
        for link in id_to_link[node.id]:
            post = link.post.upper()
            if post in ('EQ', 'NEQ'):
                arg = id_to_iv[link.end]
            elif post == 'HEQ':
                arg = id_to_lbl[link.end]
            elif post == 'H':
                arg = vfac.new(variable.HANDLE)
                hcons.append(qeq(arg, id_to_lbl[link.end]))
            else:
                continue  # ignore unknown post values?
            args[link.role] = arg
        if node.carg is not None:
            args[mrs.CONSTANT_ROLE] = node.carg
        rels.append(
            mrs.EP(node.predicate,
                   label,
                   args=args,
                   lnk=node.lnk,
                   surface=node.surface,
                   base=node.base))

    return mrs.MRS(
        top=top,
        index=index,
        rels=rels,
        hcons=hcons,
        icons=icons,
        variables=vfac.store,
        lnk=d.lnk,
        surface=d.surface,
        identifier=d.identifier)


def _dmrs_build_maps(d, vfac):
    scopes = d.scopes()
    vfac.index.update(scopes.index)  # prevent labels from being reused
    id_to_lbl = {}
    for label, ids in scopes.items():
        id_to_lbl.update((id, label) for id in ids)

    id_to_iv = {}
    for p, q in d.quantifier_map().items():
        node = d[p]
        iv = vfac.new(node.type, node.properties)
        id_to_iv[p] = iv
        if q is not None:
            id_to_iv[q] = iv

    id_to_link = {node.id: [] for node in d.nodes}
    for link in d.links:
        id_to_link[link.start].append(link)

    return id_to_lbl, id_to_iv, id_to_link
