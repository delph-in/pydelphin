
"""
Elementary Dependency Structures (EDS).
"""

from typing import Iterable

from delphin.lnk import Lnk
from delphin.sembase import Predication, SemanticStructure


BOUND_VARIABLE_ROLE = 'BV'
PREDICATE_MODIFIER_ROLE = 'ARG1'


##############################################################################
##############################################################################
# EDS classes

class Node(Predication):
    """
    An EDS node.

    Args:
        id: node identifier
        predicate: semantic predicate
        type: node type (corresponds to the intrinsic variable type in MRS)
        edges: mapping of outgoing edge roles to target identifiers
        properties: morphosemantic properties
        carg: constant value (e.g., for named entities)
        lnk: surface alignment
        surface: surface string
        base: base form
    Attributes:
        id: node identifier
        predicate: semantic predicate
        type: node type (corresponds to the intrinsic variable type in MRS)
        edges: mapping of outgoing edge roles to target identifiers
        properties: morphosemantic properties
        carg: constant value (e.g., for named entities)
        lnk: surface alignment
        cfrom: surface alignment starting position
        cto: surface alignment ending position
        surface: surface string
        base: base form
    """

    __slots__ = ('edges', 'properties', 'carg')

    def __init__(self,
                 id: int,
                 predicate: str,
                 type: str = None,
                 edges: dict = None,
                 properties: dict = None,
                 carg: str = None,
                 lnk: Lnk = None,
                 surface=None,
                 base=None):

        if not edges:
            edges = {}
        if not properties:
            properties = {}

        super().__init__(id, predicate, type, lnk, surface, base)

        self.edges = edges
        self.properties = properties
        self.carg = carg

    def __eq__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return (self.predicate == other.predicate
                and self.type == other.type
                and self.edges == other.edges
                and self.properties == other.properties
                and self.carg == other.carg)


class EDS(SemanticStructure):
    """
    An Elementary Dependency Structure (EDS) instance.

    EDS are semantic structures deriving from MRS, but they are not
    interconvertible with MRS as the do not encode a notion of
    quantifier scope.

    Args:
        top: the id of the graph's top node
        nodes: an iterable of EDS nodes
        lnk: surface alignment
        surface: surface string
        identifier: a discourse-utterance identifier
    """

    __slots__ = ()

    def __init__(self,
                 top: str = None,
                 nodes: Iterable[Node] = None,
                 lnk: Lnk = None,
                 surface=None,
                 identifier=None):
        if nodes is None:
            nodes = []
        super().__init__(top, list(nodes), lnk, surface, identifier)

    @property
    def nodes(self):
        """Alias of :attr:`predications`."""
        return self.predications

    @property
    def edges(self):
        """The list of all edges."""
        edges = []
        for node in self.nodes:
            edges.extend((node.id, role, target)
                         for role, target in node.edges.items())
        return edges

    # SemanticStructure methods

    def arguments(self, types=None):
        args = {}
        if types is not None:
            ntypes = {node.id: node.type for node in self.nodes}
        else:
            ntypes = {}
        for node in self.nodes:
            args[node.id] = []
            for role, target in node.edges.items():
                if types is None or ntypes.get(target) in types:
                    args[node.id].append((role, target))
        return args

    def properties(self, id):
        return self[id].properties

    def is_quantifier(self, id):
        """
        Return `True` if *id* is the id of a quantifier node.
        """
        return BOUND_VARIABLE_ROLE in self[id].edges

    def quantification_pairs(self):
        qs = set()
        qmap = {}
        for src, roleargs in self.arguments().items():
            for role, tgt in roleargs:
                if role == BOUND_VARIABLE_ROLE:
                    qs.add(src)
                    qmap[tgt] = self[src]
        pairs = []
        # first pair non-quantifiers to their quantifier, if any
        for node in self.nodes:
            if node.id not in qs:
                pairs.append((node, qmap.get(node.id)))
        # for MRS any unpaired quantifiers are added here, but in EDS
        # I'm not sure what an unpaired quantifier would look like
        return pairs
