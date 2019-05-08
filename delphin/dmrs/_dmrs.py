
from typing import Iterable

from delphin import variable
from delphin.lnk import Lnk
from delphin.sembase import Predication
from delphin import scope

TOP_NODE_ID      = 0
FIRST_NODE_ID    = 10000
RESTRICTION_ROLE = 'RSTR'  # DMRS establishes that quantifiers have a RSTR link
BARE_EQ_ROLE     = 'MOD'
EQ_POST          = 'EQ'
HEQ_POST         = 'HEQ'
NEQ_POST         = 'NEQ'
H_POST           = 'H'
NIL_POST         = 'NIL'
CVARSORT         = 'cvarsort'


class Node(Predication):
    """
    A DMRS node.

    Nodes are very simple predications for DMRSs. Nodes don't have
    arguments or labels like :class:`delphin.mrs.EP` objects, but they
    do have an attribute for CARGs and contain their vestigial
    variable type and properties in `sortinfo`.

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
        sortinfo: properties with the node type at key `"cvarsort"`
        carg: constant value (e.g., for named entities)
        lnk: surface alignment
        cfrom: surface alignment starting position
        cto: surface alignment ending position
        surface: surface string
        base: base form
    """

    __slots__ = ('type', 'properties', 'carg')

    def __init__(self,
                 id: int,
                 predicate: str,
                 type: str = None,
                 properties: dict = None,
                 carg: str = None,
                 lnk: Lnk = None,
                 surface=None,
                 base=None):
        if not isinstance(id, int):
            raise TypeError('node id must be of type int')
        id = id
        super().__init__(id, predicate, lnk, surface, base)
        self.type = type
        if not properties:
            properties = {}
        self.properties = properties
        self.carg = carg

    @property
    def sortinfo(self):
        """
        Morphosemantic property mapping with cvarsort.
        """
        d = dict(self.properties)
        if self.type is not None:
            d[CVARSORT] = self.type
        return d

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


class Link(object):
    """
    DMRS-style dependency link.

    Links are a way of representing arguments without variables. A
    Link encodes a start and end node, the role name, and the scopal
    relationship between the start and end (e.g. label equality, qeq,
    etc).

    Args:
        start: node id of the start of the Link
        end: node id of the end of the Link
        role: role of the argument
        post: "post-slash label" indicating the scopal
            relationship between the start and end of the Link;
            possible values are `NEQ`, `EQ`, `HEQ`, and `H`
    Attributes:
        start: node id of the start of the Link
        end: node id of the end of the Link
        role: role of the argument
        post: "post-slash label" indicating the scopal
            relationship between the start and end of the Link
    """

    __slots__ = ('start', 'end', 'role', 'post')

    def __init__(self, start: int, end: int, role: str, post: str):
        if not (isinstance(start, int) and isinstance(end, int)):
            raise TypeError('start and end node ids must be of type int')
        self.start = start
        self.end = end
        self.role = role
        self.post = post

    def __repr__(self):
        return '<Link object ({} :{}/{} {}) at {}>'.format(
            self.start, self.role or '', self.post, self.end, id(self)
        )

    def __eq__(self, other):
        if not isinstance(other, Link):
            return NotImplemented
        return (self.start == other.start
                and self.end == other.end
                and self.role == other.role
                and self.post == other.post)

    def __ne__(self, other):
        if not isinstance(other, Link):
            return NotImplemented
        return not self.__eq__(other)


class DMRS(scope.ScopingSemanticStructure):
    """
    Dependency Minimal Recursion Semantics (DMRS) class.

    DMRS instances have a list of Node objects and a list of Link
    objects. The scopal top node may be set directly via a parameter
    or may be implicitly set via a `/H` Link from the special node id
    `0`. If both are given, the link is ignored. The non-scopal top
    (index) node may only be set via the *index* parameter.

    Args:
        top: the id of the scopal top node
        index: the id of the non-scopal top node
        nodes: an iterable of DMRS nodes
        links: an iterable of DMRS links
        lnk: surface alignment
        surface: surface string
        identifier: a discourse-utterance identifier

    Example:

    >>> rain = Node(10000, '_rain_v_1', type='e')
    >>> heavy = Node(10001, '_heavy_a_1', type='e')
    >>> arg1_link = Link(10000, 10001, role='ARG1', post='EQ')
    >>> d = DMRS(top=10000, index=10000, [rain], [arg1_link])
    """

    __slots__ = ('links')

    def __init__(self,
                 top: int = None,
                 index: int = None,
                 nodes: Iterable[Node] = None,
                 links: Iterable[Link] = None,
                 lnk: Lnk = None,
                 surface=None,
                 identifier=None):

        top, links = _normalize_top_and_links(top, links)

        super().__init__(top, index, nodes, lnk, surface, identifier)

        self.links = links

    @property
    def nodes(self):
        """Alias of :attr:`predications`."""
        return self.predications

    def __eq__(self, other):
        if not isinstance(other, DMRS):
            return NotImplemented
        return (self.top == other.top
                and self.index == other.index
                and self.nodes == other.nodes
                and self.links == other.links)

    # SemanticStructure methods

    def properties(self, id):
        return self[id].properties

    def is_quantifier(self, id):
        """
        Return `True` if *id* is the id of a quantifier node.
        """
        return any(link.role == RESTRICTION_ROLE
                   for link in self.links if link.start == id)

    def quantifier_map(self):
        qmap = {node.id: None for node in self.nodes}
        for link in self.links:
            if link.role == RESTRICTION_ROLE:
                qmap[link.end] = link.start
        return qmap

    # ScopingSemanticStructure methods

    def arguments(self, types=None, scopal=None):
        args = {}
        id_to_type = {}
        for node in self.nodes:
            args[node.id] = {}
            id_to_type[node.id] = node.type
        _scposts = (H_POST, HEQ_POST)

        for link in self.links:
            if link.role == BARE_EQ_ROLE:  # not an argument
                continue
            if types and id_to_type.get(link.end) not in types:
                continue
            if scopal is not None and scopal != (link.post in _scposts):
                continue
            # all tests passed
            args[link.start][link.role] = link.end

        return args

    def scopes(self):
        vfac, h = variable.VariableFactory(starting_vid=0), variable.HANDLE
        prescopes = {vfac.new(h): []}  # implicit top; top never has nodes
        id_to_lbl = {node.id: vfac.new(h) for node in self.nodes}
        prescopes.update((label, [id]) for id, label in id_to_lbl.items())
        leqs = [(id_to_lbl[link.start], id_to_lbl[link.end])
                for link in self.links if link.post == EQ_POST]
        return scope.conjoin(prescopes, leqs)

    def scope_constraints(self, scopes=None):
        if scopes is None:
            scopes = self.scopes()

        id_to_lbl = {}
        top = None
        for label, ids in scopes.items():
            if not ids:
                top = label  # top is the only scope with no nodes
            else:
                for id in ids:
                    id_to_lbl[id] = label

        if top:
            cons = [(top, scope.QEQ, id_to_lbl[self.top])]
        for link in self.links:
            hi = id_to_lbl[link.start]
            lo = id_to_lbl[link.end]
            if link.post == HEQ_POST:
                cons.append((hi, scope.LHEQ, lo))
            elif link.post == H_POST:
                cons.append((hi, scope.QEQ, lo))

        return cons


def _normalize_top_and_links(top, links):
    """
    Original DMRS had a /H link from a special node id of 0 to
    indicate the top node, but now the `top` attribute is used.
    Remove any such links and use them to specify `top` if it was not
    specified already (otherwise ignore them).
    """
    _links = []
    if links is not None:
        for link in links:
            if link.start == TOP_NODE_ID:
                if top is None:
                    top = link.end
            else:
                _links.append(link)
    return top, _links
