
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

    __slots__ = ('properties', 'carg')

    def __init__(self,
                 id: int,
                 predicate: str,
                 type: str = None,
                 properties: dict = None,
                 carg: str = None,
                 lnk: Lnk = None,
                 surface=None,
                 base=None):
        id = int(id)
        super().__init__(id, predicate, type, lnk, surface, base)
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
        self.start = int(start)
        self.end = int(end)
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

    Attributes:
        top: The scopal top node.
        index: The non-scopal top node.
        nodes: The list of Nodes (alias of
            :attr:`~delphin.sembase.SemanticStructure.predications`).
        links: The list of Links.
        lnk: The surface alignment for the whole MRS.
        surface: The surface string represented by the MRS.
        identifier: A discourse-utterance identifier.

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

        if top:
            top = int(top)
        if index:
            index = int(index)
        if nodes is None:
            nodes = []

        super().__init__(top, index, list(nodes), lnk, surface, identifier)

        self.links = links

    @property
    def nodes(self):
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

    def quantification_pairs(self):
        qs = set()
        qmap = {}
        for link in self.links:
            if link.role == RESTRICTION_ROLE:
                qs.add(link.start)
                qmap[link.end] = self[link.start]
        pairs = []
        # first pair non-quantifiers to their quantifier, if any
        for node in self.nodes:
            if node.id not in qs:
                pairs.append((node, qmap.get(node.id)))
        # for MRS any unpaired quantifiers are added here, but in DMRS
        # I'm not sure what an unpaired quantifier would look like;
        # its link.end must point to something
        return pairs

    def arguments(self, types=None, expressed=None):
        """
        Return a mapping of the argument structure.

        When *types* is used, any DMRS Links with :attr:`Link.attr`
        set to :data:`H_POST` or :data:`HEQ_POST` are considered to
        have a type of `'h'`, so one can exclude scopal arguments by
        omitting `'h'` on *types*. Otherwise an argument's type is the
        :attr:`Node.type` of the link's target.

        Args:
            types: an iterable of predication types to include
            expressed: if `True`, only include arguments to expressed
                predications; if `False`, only include those
                unexpressed; if `None`, include both
        Returns:
            A mapping of predication ids to lists of (role, target)
            pairs for outgoing arguments for the predication.
        """

        args = {node.id: [] for node in self.nodes}
        H = variable.HANDLE

        for link in self.links:
            # MOD/EQ links are not arguments
            if link.role == BARE_EQ_ROLE:
                continue
            # ignore undesired argument types
            if types:
                if link.post in (H_POST, HEQ_POST):
                    if H not in types:
                        continue
                else:
                    node = self[link.end]
                    if node.type is None or node.type not in types:
                        continue
            # currently DMRS cannot encode unexpressed arguments
            if expressed is not None and not expressed:
                continue
            args[link.start].append((link.role, link.end))

        return args

    # ScopingSemanticStructure methods

    def scopes(self):
        """
        Return a tuple containing the top label and the scope map.

        Note that the top label is different from :attr:`top`, which
        the top node's id. If :attr:`top` does not select a top node,
        the `None` is returned for the top label.

        The scope map is a dictionary mapping scope labels to the
        lists of predications sharing a scope.
        """

        h = variable.HANDLE
        vfac = variable.VariableFactory(starting_vid=1)

        id_to_lbl = {node.id: vfac.new(h) for node in self.nodes}

        leqs = [(id_to_lbl[link.start], id_to_lbl[link.end])
                for link in self.links
                if link.post == EQ_POST]
        prescopes = {id_to_lbl[node.id]: [node] for node in self.nodes}

        scopes = scope.conjoin(prescopes, leqs)
        top = None
        if self.top is not None:
            top_node = self[self.top]
            top = next((label for label, nodes in scopes.items()
                        if top_node in nodes),
                       None)

        return top, scopes

    def scopal_arguments(self, scopes=None):
        """
        Return a mapping of the scopal argument structure.

        The return value maps node ids to lists of scopal arguments as
        (role, scope_relation, target) triples. If *scopes* is given,
        the target is the scope label, otherwise it is the target
        node's id. Note that ``MOD/EQ`` links are not included as
        scopal arguments.

        Args:
            scopes: mapping of scope labels to lists of predications
        Example:
            >>> d = DMRS(...)  # for "It doesn't rain.
            >>> d.scopal_arguments()
            {10000: [('ARG1', 'qeq', 10001)]}
            >>> top, scopes = d.scopes()
            >>> d.scopal_arguments(scopes=scopes)
            {10000: [('ARG1', 'qeq', 'h2')]}
        """
        id_to_lbl = {}
        if scopes is not None:
            for label, nodes in scopes.items():
                for node in nodes:
                    id_to_lbl[node.id] = label

        scargs = {node.id: [] for node in self.nodes}
        for link in self.links:
            if link.post == HEQ_POST:
                relation = scope.LHEQ
            elif link.post == H_POST:
                relation = scope.QEQ
            else:
                continue
            # get the label if scopes was given
            target = id_to_lbl.get(link.end, link.end)
            scargs[link.start].append((link.role, relation, target))

        return scargs


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
