
"""
Elementary Dependency Structures (EDS).
"""

from typing import Iterable

from delphin.lnk import Lnk, LnkMixin

BOUND_VARIABLE_ROLE     = 'BV'
PREDICATE_MODIFIER_ROLE = 'ARG1'


##############################################################################
##############################################################################
# EDS classes

class Node(LnkMixin):
    """
    An EDS node.

    Args:
        id: node identifier
        predicate: semantic predicate
        type: node type (corresponds to the intrinsic variable type in MRS)
        properties: morphosemantic properties
        carg: constant value (e.g., for named entities)
        lnk: surface alignment
        surface: surface string
        base: base form
    Attributes:
        id: node identifier
        predicate: semantic predicate
        type: node type (corresponds to the intrinsic variable type in MRS)
        properties: morphosemantic properties
        carg: constant value (e.g., for named entities)
        lnk: surface alignment
        cfrom: surface alignment starting position
        cto: surface alignment ending position
        surface: surface string
        base: base form
    """

    __slots__ = ('id', 'predicate', 'type', 'properties', 'carg',
                 'lnk', 'surface', 'base')

    def __init__(self,
                 id: int,
                 predicate: str,
                 type: str = None,
                 properties: dict = None,
                 carg: str = None,
                 lnk: Lnk = None,
                 surface=None,
                 base=None):
        self.id = id
        self.predicate = predicate
        self.type = type
        if not properties:
            properties = {}
        self.properties = properties
        self.carg = carg
        if lnk is None:
            lnk = Lnk.default()
        self.lnk = lnk
        self.surface = surface
        self.base = base

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return (self.predicate == other.predicate
                and self.type == other.type
                and self.properties == other.properties
                and self.carg == other.carg)

    def __ne__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return not (self == other)


class Edge(object):
    """
    EDS-style dependency edges.

    Args:
        start: node id of the start of the edge
        end: node id of the end of the edge
        role: role of the argument
    Attributes:
        start: node id of the start of the edge
        end: node id of the end of the edge
        role: role of the argument
    """

    __slots__ = ('start', 'end', 'role')

    def __init__(self, start: str, end: str, role: str):
        self.start = start
        self.end = end
        self.role = role

    def __eq__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return (self.start == other.start
                and self.end == other.end
                and self.role == other.role)

    def __ne__(self, other):
        if not isinstance(other, Edge):
            return NotImplemented
        return not self.__eq__(other)


class EDS(LnkMixin):
    """
    An Elementary Dependency Structure (EDS) instance.

    EDS are semantic structures deriving from MRS, but they are not
    interconvertible with MRS as the do not encode a notion of
    quantifier scope.

    Args:
        top: the id of the graph's top node
        nodes: an iterable of EDS nodes
        edges: an iterable of EDS edges
    """

    __slots__ = ('top', 'nodes', 'edges')

    def __init__(self,
                 top: str = None,
                 nodes: Iterable[Node] = None,
                 edges: Iterable[Edge] = None):
        if nodes is None: nodes = []
        if edges is None: edges = []

        self.top = top
        self.nodes = nodes
        self.edges = edges

    def __eq__(self, other):
        if not isinstance(other, EDS):
            return NotImplemented
        return (self.top == other.top
                and self.nodes == other.nodes
                and self.edges == other.edges)

    def __ne__(self, other):
        if not isinstance(other, EDS):
            return NotImplemented
        return not (self == other)

    def is_quantifier(self, node_id):
        """
        Return `True` if *node_id* is the id of a quantifier node.
        """
        return any(edge.role == BOUND_VARIABLE_ROLE
                   for edge in self.edges if edge.start == node_id)
