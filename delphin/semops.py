
from functools import singledispatch

from delphin.exceptions import PyDelphinException
from delphin import variable
from delphin import predicate
from delphin import sembase
from delphin import scope
from delphin import mrs
from delphin import dmrs
from delphin import eds
from delphin.util import (
    _connected_components
)


# Exceptions

class SemanticOperationError(PyDelphinException):
    """Raised on an invalid semantic operation."""


# Isomorphism Checking

@singledispatch
def is_isomorphic(x1: sembase.SemanticStructure,
                  x2: sembase.SemanticStructure,
                  properties: bool = True) -> bool:
    """
    Return `True` if *x1* and *x2* are isomorphic semantic structures.

    Isomorphicity compares the predicates of a semantic structure, the
    morphosemantic properties of their predicate instances (if
    `properties=True`), constant arguments, and the argument structure
    between predicate instances. Non-graph properties like identifiers
    and surface alignments are ignored.

    Args:
        x1: the left semantic structure to compare
        x2: the right semantic structure to compare
        properties: if `True`, ensure variable properties are
            equal for mapped predicate instances
    """
    raise SemanticOperationError(
        'computation of isomorphism for {} objects is not defined'
        .format(x1.__class__.__name__))


@is_isomorphic.register(mrs.MRS)
def _is_mrs_isomorphic(m1, m2, properties=True):
    import networkx as nx

    if not isinstance(m2, mrs.MRS):
        raise SemanticOperationError(
            'second argument is not an MRS object: {}'
            .format(m2.__class__.__name__))

    m1dg = _make_mrs_digraph(m1, nx.DiGraph(), properties)
    m2dg = _make_mrs_digraph(m2, nx.DiGraph(), properties)

    def nem(m1d, m2d):  # node-edge-match
        return m1d.get('sig') == m2d.get('sig')

    return nx.is_isomorphic(m1dg, m2dg, node_match=nem, edge_match=nem)


def _make_mrs_digraph(x, dg, properties):
    # scope labels (may be targets of arguments or hcons)
    for label, eps in x.scopes().items():
        dg.add_edges_from((label, ep.iv, {'sig': 'eq-scope'}) for ep in eps)
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


# Conversion Routines

def mrs_to_dmrs(m: mrs.MRS):
    """
    MRS to DMRS conversion

    In order for MRS to DMRS conversion to work, the MRS must satisfy
    the **intrinsic variable property**.

    Args:
        m: the input MRS
    Returns:
        DMRS
    Raises:
        SemanticOperationError: when the *m* cannot be converted
    """
    # keep ids consistent
    idmap = {ep.id: i for i, ep in enumerate(m.rels, dmrs.FIRST_NODE_ID)}
    nodes, ivmap = _mrs_to_nodes(dmrs.Node, m, idmap)
    links, top = _mrs_to_links(dmrs.Link, m, idmap, ivmap)
    index = ivmap[m.index] if m.index else None
    return dmrs.DMRS(
        top=top,
        index=index,
        nodes=nodes,
        links=links,
        lnk=m.lnk,
        surface=m.surface,
        identifier=m.identifier)


def _mrs_to_nodes(cls, m, idmap):
    nodes = []
    ivmap = {}
    for ep in m.rels:
        node_id = idmap[ep.id]
        iv = ep.iv
        nodes.append(
            cls(node_id,
                ep.predicate,
                variable.type(iv),
                m.properties(iv),
                ep.carg,
                ep.lnk,
                ep.surface,
                ep.base))
        if not ep.is_quantifier():
            ivmap[iv] = node_id
    return nodes, ivmap


def _mrs_to_links(cls, m, idmap, ivmap):
    links = []
    hcmap = {hc.hi: hc for hc in m.hcons}
    reps = scope.representatives(m)

    top = None
    if m.top in hcmap:
        lbl = hcmap[m.top].lo
        rep = reps[lbl][0]
        top = idmap[rep]
    elif m.top in reps:
        rep = reps[top][0]
        top = idmap[rep]

    for src, roleargs in m.arguments().items():
        start = idmap[src]
        for role, tgt in roleargs.items():

            if tgt in ivmap:
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

            end = ivmap[tgt]
            links.append(cls(start, end, role, post))

    return links, top


def dmrs_to_mrs(d: dmrs.DMRS):
    pass


def mrs_to_eds(m: mrs.MRS, predicate_modifiers=True):
    pass


def dmrs_to_eds(d: dmrs.DMRS):
    pass


# Structure Inspection

def is_connected(x: sembase.SemanticStructure) -> bool:
    pass


def has_intrinsic_variable_property(m: mrs.MRS) -> bool:
    pass

