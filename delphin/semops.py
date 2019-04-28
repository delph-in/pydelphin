
from functools import singledispatch

import networkx as nx

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
    if not isinstance(m2, mrs.MRS):
        raise SemanticOperationError(
            'second argument is not an MRS object: {}'
            .format(m2.__class__.__name__))

    m1dg = _make_mrs_digraph(m1, properties)
    m2dg = _make_mrs_digraph(m2, properties)

    def nem(m1d, m2d):  # node-edge-match
        return m1d.get('sig') == m2d.get('sig')

    return nx.is_isomorphic(m1dg, m2dg, node_match=nem, edge_match=nem)


def _make_mrs_digraph(x, properties):
    dg = nx.DiGraph()
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
    _non_link_roles = {mrs.INTRINSIC_ROLE, mrs.CONSTANT_ROLE}
    eps = list(enumerate(m.rels, dmrs.FIRST_NODE_ID))  # keep ids consistent
    representatives = scope.representatives(m)
    nodes, ivmap = _mrs_to_nodes(dmrs.Node, m, eps)
    links = _mrs_to_links(dmrs.Link, m, eps, ivmap)
    return dmrs.DMRS(
        top=top,
        index=index,
        nodes=nodes,
        links=links,
        lnk=m.lnk,
        surface=m.surface,
        identifier=m.identifier)


def _mrs_to_nodes(cls, m, eps):
    nodes = []
    ivmap = {}
    for node_id, ep in eps:
        iv = ep.iv
        nodes.append(
            cls(node_id,
                ep.predicate,
                variable.type(iv),
                properties,
                ep.carg,
                ep.lnk,
                ep.surface,
                ep.base))
        if not ep.is_quantifier():
            ivmap[iv] = node_id
    return nodes, ivmap


def _mrs_to_links(cls, m, eps, ivmap):
    links = []
    scopetree = m.scopetree()
    for src_id, ep in eps:
        for role, value in ep.args.items():
            if role in _non_link_roles:
                continue
            links.append(cls(src_id, tgt_id, role, post))


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


# def mrs_scope_representatives(mrs):
#     nested_scopes = mrs_nested_scopes(mrs)

#     if scopeid not in self._scope_reps:
#         scope_nodeids = self.scopes[scopeid]
#         if len(scope_nodeids) == 1:
#             self._scope_reps[scopeid] = list(scope_nodeids)
#         else:
#             nested_scope = self._nested_scope(scopeid)
#             candidates = []
#             for nodeid in scope_nodeids:
#                 edges = [edge for edge in self.edgemap.get(nodeid, [])
#                          if edge.mode == _Edge.VARARG]
#                 if all(edge.end not in nested_scope for edge in edges):
#                     candidates.append(nodeid)
#             if len(candidates) > 1:
#                 qs = set(self.qeqmap).union(self.qeqmap.values())
#                 rank = {}
#                 for nodeid in candidates:
#                     node = self.nodemap[nodeid]
#                     if nodeid in qs:
#                         rank[nodeid] = 0
#                     elif node.predicate.type == Predicate.ABSTRACT:
#                         rank[nodeid] = 2
#                     elif nodeid :
#                         rank[nodeid] = 1
#                 candidates.sort(key=lambda n: rank[n])
#             self._scope_reps = candidates
#         return self._scope_reps[scopeid]

# def _nested_scope(self, scopeid):
#     if scopeid not in self._nested_scopes:
#         self._nested_scopes[scopeid] = ns = set(self.scopes[scopeid])
#         for nodeid in list(ns):
#             for edge in self.edgemap.get(nodeid, []):
#                 if edge.mode in (_Edge.LBLARG, _Edge.QEQARG):
#                     ns.update(self._nested_scope(edge.end))
#     return self._nested_scopes[scopeid]


# class _XMRS(_SemanticComponent):
#     """
#     Args:
#         top (int): scopeid of top scope
#         index (str): nodeid of top predication
#         xarg (str): nodeid of external argument
#         nodes (list): list of :class:`_Node` objects
#         scopes (dict): map of scopeid (e.g., a label) to a set of nodeids
#         edges (list): list of (nodeid, role, mode, target) tuples
#         icons (list): list of (source, relation, target) tuples
#         lnk: surface alignment of the whole structure
#         surface: surface form of the whole structure
#         identifier: corpus-level identifier
#     """
#     def __init__(self, top, index, xarg,
#                  nodes, scopes, edges, icons,
#                  lnk, surface, identifier):
#         super(_XMRS, self).__init__(top, index, xarg, lnk, surface, identifier)
#         self.nodes = nodes
#         self.scopes = scopes
#         self.edges = edges
#         self.icons = icons

#         self.nodemap = {node.nodeid: node for node in nodes}

#         self.scopemap = {}
#         for scopeid, nodeids in scopes.items():
#             for nodeid in nodeids:
#                 self.scopemap[nodeid] = scopeid
#         self._nested_scopes = {}
#         self._scope_reps = {}

#         self.edgemap = {node.nodeid: {} for node in nodes}
#         self.quantifiermap = {}
#         self.ivmap = {}
#         for edge in self.edges:
#             self.edgemap[edge.start][edge.role] = edge
#             if edge.role == 'RSTR':
#                 self.quantifiermap[edge.start] = edge.end
#             elif edge.mode == _Edge.INTARG:
#                 self.ivmap[edge.start] = edge.end

#     def is_quantifier(self, nodeid):
#         return nodeid in self.quantifiermap

#     def scope_representative(self, scopeid):
#         reps = self.scope_representatives(scopeid)
#         if reps:
#             return reps[0]
#         return None

#     def scope_representatives(self, scopeid):
#         if scopeid not in self._scope_reps:
#             scope_nodeids = self.scopes[scopeid]
#             if len(scope_nodeids) == 1:
#                 self._scope_reps[scopeid] = list(scope_nodeids)
#             else:
#                 nested_scope = self._nested_scope(scopeid)
#                 candidates = []
#                 for nodeid in scope_nodeids:
#                     edges = [edge for edge in self.edgemap.get(nodeid, [])
#                              if edge.mode == _Edge.VARARG]
#                     if all(edge.end not in nested_scope for edge in edges):
#                         candidates.append(nodeid)
#                 if len(candidates) > 1:
#                     qs = set(self.qeqmap).union(self.qeqmap.values())
#                     rank = {}
#                     for nodeid in candidates:
#                         node = self.nodemap[nodeid]
#                         if nodeid in qs:
#                             rank[nodeid] = 0
#                         elif node.predicate.type == Predicate.ABSTRACT:
#                             rank[nodeid] = 2
#                         elif nodeid :
#                             rank[nodeid] = 1
#                     candidates.sort(key=lambda n: rank[n])
#                 self._scope_reps = candidates
#         return self._scope_reps[scopeid]

#     def _nested_scope(self, scopeid):
#         if scopeid not in self._nested_scopes:
#             self._nested_scopes[scopeid] = ns = set(self.scopes[scopeid])
#             for nodeid in list(ns):
#                 for edge in self.edgemap.get(nodeid, []):
#                     if edge.mode in (_Edge.LBLARG, _Edge.QEQARG):
#                         ns.update(self._nested_scope(edge.end))
#         return self._nested_scopes[scopeid]
