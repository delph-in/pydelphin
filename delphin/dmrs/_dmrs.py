
from typing import Iterable

from delphin.lnk import Lnk, LnkMixin

TOP_NODE_ID      = 0
FIRST_NODE_ID    = 10000
RESTRICTION_ROLE = 'RSTR' # DMRS establishes that quantifiers have a RSTR link
EQ_POST          = 'EQ'
HEQ_POST         = 'HEQ'
NEQ_POST         = 'NEQ'
H_POST           = 'H'
NIL_POST         = 'NIL'
CVARSORT         = 'cvarsort'
BARE_EQ_ROLE     = 'MOD'


class Node(LnkMixin):
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
        return '<Link object (#{} :{}/{} #{}) at {}>'.format(
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


class DMRS(LnkMixin):
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

    __slots__ = ('top', 'index', 'nodes', 'links',
                 'lnk', 'surface', 'identifier')

    def __init__(self,
                 top: int = None,
                 index: int = None,
                 nodes: Iterable[Node] = None,
                 links: Iterable[Link] = None,
                 lnk: Lnk = None,
                 surface=None,
                 identifier=None):
        top, links = _normalize_top_and_links(top, links)
        self.top = top
        self.index = index
        if nodes is None:
            nodes = []
        self.nodes = nodes
        self.links = links
        if lnk is None:
            lnk = Lnk.default()
        self.lnk = lnk
        self.surface = surface
        self.identifier = identifier

    def __eq__(self, other):
        if not isinstance(other, DMRS):
            return NotImplemented
        return (self.top == other.top
                and self.index == other.index
                and self.nodes == other.nodes
                and self.links == other.links)

    def __ne__(self, other):
        if not isinstance(other, DMRS):
            return NotImplemented
        return not (self == other)

    def is_quantifier(self, node_id):
        """
        Return `True` if *node_id* is the id of a quantifier node.
        """
        return any(link.role == RESTRICTION_ROLE
                   for link in self.links if link.start == node_id)


def _normalize_top_and_links(top, links):
    _links = []
    if links is not None:
        for link in links:
            if link.start == TOP_NODE_ID:
                if top is None:
                    top = link.end
            else:
                _links.append(link)
    return top, _links
