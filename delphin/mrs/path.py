#import pdb
import re
from collections import deque, defaultdict
from itertools import product

from .components import Pred
from .util import powerset
from delphin._exceptions import XmrsError
# for rebuilding Xmrs from paths
from delphin.mrs import Node, Link, Pred, Dmrs

TOP = 'TOP'
STAR = '*'

# flags
NODEID = NID = 1
PRED = P = 2
VARSORT = VS = 4
VARPROPS = VP = 8
SUBPATHS = SP = 16
OUTAXES = OUT = 32
INAXES = IN = 64
UNDIRECTEDAXES = UND = 128
CONTEXT = VS | VP | SP
ALLAXES = OUT | IN | UND
DEFAULT = P | VS | VP | SP | OUT | IN
ALL = NID | P | VS | VP | SP | OUT | IN | UND

class XmrsPathError(XmrsError): pass


# GRAPH WALKING ########################################################

def axis_sort(axis):
    return (
        not axis.endswith('>'),  # forward links first
        not axis.startswith('<'),  # then backward, then undirected
        not axis[1:].startswith('LBL'),  # LBL before other args
        axis[1:].startswith('BODY'),  # BODY last
        axis[1:]  # otherwise alphabtical
    )


def walk(xmrs, start=0, method='headed', sort_key=axis_sort):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))

    if start == 0 or xmrs.get_pred(start):
        yield (None, start, None)
    else:
        raise XmrsPathError('Start nodeid not in Xmrs graph.')

    linkdict = _build_linkdict(xmrs)
    for step in _walk(xmrs, start, linkdict, set(), method, sort_key):
        yield step


def _walk(xmrs, nodeid, linkdict, visited, method, sort_key):
    if nodeid in visited:
        return
    visited.add(nodeid)

    local_links = linkdict.get(nodeid, {})
    axes = sorted(_get_axes(method, local_links), key=sort_key)
    for axis in axes:
        tgtnid = local_links[axis]
        # don't follow undirected links twice
        if axis == ':/EQ:' and tgtnid in visited:
            continue
        yield (nodeid, tgtnid, axis)
        for step in _walk(xmrs, tgtnid, linkdict, visited, method, sort_key):
            yield step


def _build_linkdict(xmrs):
    links = defaultdict(dict)
    for link in xmrs.links:
        axis = '{}/{}'.format(link.argname or '', link.post)
        if link_is_directed(link):
            links[link.start][':{}>'.format(axis)] = link.end
            links[link.end]['<{}:'.format(axis)] = link.start
        else:
            # pretend they are directed
            #links[link.end]['<{}:'.format(axis)] = link.start
            links[link.start][':{}:'.format(axis)] = link.end
            links[link.end][':{}:'.format(axis)] = link.start
    return links


def _get_axes(method, links):
    # top-down: :X/Y> or :X/Y: (the latter only if added)
    if method == 'top-down':
        return [c for c in links if c.startswith(':')]
    elif method == 'bottom-up':
        return [c for c in links if c.endswith(':')]
    elif method == 'headed':
        return [c for c in links if headed(c)]


def link_is_directed(link):
    return bool(link.argname) or link.post != 'EQ'


def headed(axis):
    # quantifiers and X/EQ links are not the heads of their subgraphs
    if axis == '<RSTR/H:' or axis.endswith('/EQ:'):
        return True
    if (axis == ':RSTR/H>' or
            axis.endswith('/EQ>') or
            axis.startswith('<')):
        return False
    return True


# CLASSES ##############################################################

class XmrsPathNode(object):

    __slots__ = ('nodeid', 'pred', 'context', 'links')

    def __init__(self, nodeid, pred, context=None, links=None):
        self.nodeid = nodeid
        self.pred = pred
        self.context = dict(context or [])
        self.links = dict(links or [])

    def __getitem__(self, key):
        return self.links[key]

    def __iter__(self):
        return iter(self.links.items())

    def update(self, other):
        self.nodeid = other.nodeid or self.nodeid
        self.pred = other.pred or self.pred
        self.context.update(other.context or [])
        for axis, tgt in other.links.items():
            if not self.links.get(axis):
                self.links[axis] = tgt
            else:
                self[axis].update(tgt)

    # def extend(self, extents):
    #     for axes, extent in extents:
    #         # the final axis may be new information
    #         tgt = self.follow(axes[:-1])
    #         if axes:
    #             subtgt = tgt.links.get(axes[-1])
    #             if subtgt is None:
    #                 tgt.links[axes[-1]] = extent
    #                 continue
    #             else:
    #                 tgt = subtgt
    #         tgt.update(extent)


class XmrsPath(XmrsPathNode):

    def __init__(self, nodeid, pred, context=None, links=None):
        XmrsPathNode.__init__(self, nodeid, pred, context, links)
        self.calculate_metrics()

    @classmethod
    def from_node(cls, node):
        return cls(node.nodeid, node.pred, node.context, node.links)

    def calculate_metrics(self):
        self._distance = {}
        self._depth = {}
        self._preds = {}
        self._calculate_metrics(self, 0, 0)

    def _calculate_metrics(self, curnode, depth, distance):
        if curnode is None:
            return
        # add pred index
        try:
            self._preds[curnode.pred].append(curnode)
        except KeyError:
            self._preds[curnode.pred] = []
            self._preds[curnode.pred].append(curnode)
        _id = id(curnode)
        # we may re-update if we're on a shorter path
        updated = False
        if _id not in self._distance or distance < self._distance[_id]:
            self._distance[_id] = distance
            updated = True
        if _id not in self._depth or abs(depth) < abs(self._depth[_id]):
            self._depth[_id] = depth
            updated = True
        if not updated:
            return
        for link in curnode.links:
            if link.endswith('>'):
                self._calculate_metrics(curnode[link], depth+1, distance+1)
            elif link.startswith('<'):
                self._calculate_metrics(curnode[link], depth-1, distance+1)
            else:
                self._calculate_metrics(curnode[link], depth, distance+1)

    def distance(self, node=None):
        if node is None:
            return max(self._distance.values())
        else:
            return self._distance[id(node)]

    def depth(self, node=None, direction=max):
        if node is None:
            return direction(self._depth.values())
        return self._depth[id(node)]

    def select(self, pred):
        return self._preds.get(pred, [])

    # def extend(self, extents, base_axes=None):
    #     if base_axes is None:
    #         base_axes = []
    #     base = self.follow(base_axes)
    #     base.extend(extents)
    #     self.calculate_metrics()


# HELPER FUNCTIONS ##########################################################


def get_nodeids(node):
    yield node.nodeid
    for link, path_node in node:
        if path_node is None:
            continue
        for nid in get_nodeids(path_node):
            yield nid


def get_preds(node):
    yield node.pred
    for link, path_node in node:
        if path_node is None:
            continue
        for pred in get_preds(path_node):
            yield pred


def copy(node, depth=-1, flags=ALL):
    nodeid = node.nodeid if (flags & NODEID) else None
    pred = node.pred if (flags & PRED) else None
    context = dict(
        (k, v) for k, v in node.context.items()
        if (k == 'varsort' and (flags & VARSORT)) or
           (k.startswith('@') and (flags & VARPROPS)) or
           (k[0] in (':', '<') and (flags & SUBPATHS))
    )
    links = {}
    if depth != 0:
        for axis, tgt in node.links.items():
            if (tgt is None and _valid_axis(axis, flags)):
                links[axis] = None
            elif (flags & SUBPATHS):
                links[axis] = copy(tgt, depth-1, flags=flags)
    n = XmrsPathNode(nodeid, pred, context=context, links=links)
    return n


def _valid_axis(axis, flags):
    return (
        (axis.endswith('>') and (flags & OUTAXES)) or
        (axis.startswith('<') and (flags & INAXES)) or
        (axis.endswith(':') and (flags & UNDIRECTEDAXES))
    )


def follow(obj, axes):
    axes = list(reversed(axes))
    while axes:
        obj = obj[axes.pop()]
    return obj


def merge(base, obj, location=None):
    """
    merge is like XmrsPathNode.update() except it raises errors on
    unequal non-None values.
    """
    # pump object to it's location with dummy nodes
    while location:
        axis = location.pop()
        obj = XmrsPathNode(None, None, links={axis: obj})
    if base is None:
        return obj
    _merge(base, obj)
    # if isinstance(base, XmrsPath):
    #     base.calculate_metrics()
    return base

def _merge(basenode, objnode):
    if basenode is None or objnode is None:
        return basenode or objnode
    basenode.nodeid = _merge_atom(basenode.nodeid, objnode.nodeid)
    basenode.pred = _merge_atom(basenode.pred, objnode.pred)
    baseside = basenode.context
    for k, v in objnode.context.items():
        if k[0] in (':', '<'):  # subpath context; need to recurse
            baseside[k] = _merge(baseside.get(k), v)
        else:
            baseside[k] = _merge_atom(baseside.get(k), v)
    baseside = basenode.links
    for axis, tgt in objnode.links.items():
        baseside[axis] = _merge(baseside.get(axis), tgt)
    return basenode


def _merge_atom(obj1, obj2):
    if obj1 is None or obj1 == STAR:
        return obj2 or obj1  # or obj1 in case obj2 is None and obj1 == STAR
    elif obj2 is None or obj2 == STAR:
        return obj1 or obj2  # or obj2 in case obj1 is None and obj2 == STAR
    elif obj1 == obj2:
        return obj1
    else:
        raise XmrsPathError(
            'Cannot merge MrsPath atoms: {} and {}'.format(obj1, obj2)
        )


# WRITING PATHS #############################################################

def format(node, sort_key=axis_sort, depth=-1, flags=DEFAULT):
    if node is None:
        return ''
    symbol = ''
    if (flags & PRED) and node.pred is not None:
        symbol = str(node.pred)
    nodeid = ''
    if (flags & NODEID) and node.nodeid is not None:
        nodeid = '#{}'.format(node.nodeid)
    if not (symbol or nodeid):
        symbol = STAR
    context = _format_context(node, sort_key, depth, flags)
    subpath = ''
    if (flags & SUBPATHS) and depth != 0:
        subpath = _format_subpath(node, sort_key, depth-1, flags)
    return '{}{}{}{}'.format(symbol, nodeid, context, subpath)


def _format_context(node, sort_key, depth, flags):
    context = ''
    if (flags & CONTEXT) and node.context:
        contexts = []
        for k in sorted(node.context, key=_context_sort):
            v = node.context[k]
            if k == 'varsort':
                if (flags & VARSORT):
                    contexts.append(v)
            elif k.startswith('@'):
                if (flags & VARPROPS):
                    contexts.append('{}={}'.format(k, v))
            elif k[0] in (':', '<'):
                if (flags & SUBPATHS):
                    contexts.append(
                        '{}{}'.format(
                            k, format(v, sort_key, depth-1, flags)
                        )
                    )
            else:
                raise XmrsPathError('Invalid context key: {}'.format(k))
        if contexts:
            context = '[{}]'.format(' & '.join(contexts))
    return context


def _format_subpath(node, sort_key, depth, flags):
    links = []
    axes = node.links.keys()
    if sort_key:
        axes = sorted(axes, key=sort_key)
    for axis in axes:
        tgt = node.links[axis]
        if (tgt or _valid_axis(axis, flags)):
            links.append(
                '{}{}'.format(
                    axis,
                    format(tgt, sort_key, depth, flags)
                )
            )
    if len(links) > 1:
        subpath = '({})'.format(' & '.join(links))
    else:
        subpath = ''.join(links)  # possibly just ''
    return subpath


def _context_sort(k):
    return (k != 'varsort', k.startswith(':'), k.startswith('<'), k)


# FINDING PATHS #############################################################

# 'named_rel:CARG'  == 'Kim'
# 'named_rel[:CARG="Kim"]'  == EP
# '_chase_v_1_rel:ARG2'  == 'x4'
# '_chase_v_1_rel:ARG2>'  == EP
# '_chase_v_1_rel:ARG2/NEQ>'  == EP
# '_chase_v_1_rel[:ARG1/NEQ>"_dog_n_1_rel" :ARG2]:ARG2/NEQ'
# 'dog_n_rel#10000[e & :CARG="Dog" & @NUM=sg]:ARG1/NEQ>blah'

def find_paths(
        xmrs,
        nodeids=None,
        method='top-down',
        flags=DEFAULT,
        max_distance=-1):
    if nodeids is None: nodeids = [0] + xmrs.nodeids  # 0 for TOP
    stepmap = defaultdict(lambda: dict())
    for startnid in nodeids:
        if startnid in stepmap:
            continue  # start node already done
        for start, end, axis in walk(xmrs, start=startnid, method=method):
            if axis in stepmap.get(start, {}):
                continue  # current node already done
            stepmap[start][axis] = end
    for nodeid in nodeids:
        for node in _find_paths(
                xmrs, stepmap, nodeid, flags, max_distance, set()):
            #yield XmrsPath.from_node(node)
            yield node


def _find_paths(
        xmrs,
        stepmap,
        start,
        flags,
        max_distance,
        visited):
    if start in visited or max_distance == 0:
        return
    visited = visited.union([start])
    ctext = None
    if start == 0:
        symbol = TOP
    else:
        node = xmrs.get_node(start)
        symbol = node.pred
        if (flags & CONTEXT):
            ctext = dict(
                [('varsort', node.cvarsort)] +
                [('@{}'.format(k), v) for k, v in node.properties.items()]
            )
    steps = stepmap.get(start, {})

    # exclude TOP from being its own path node
    if start != 0:
        yield XmrsPathNode(
            start,
            symbol,
            context=ctext,
            links={c: None for c in steps.keys()}
        )

    subpaths = {}
    for axis, tgtnid in steps.items():
        if not (flags & UNDIRECTEDAXES) and axis == ':/EQ:':
            continue
        if tgtnid == 0:
            subpaths[axis] = [XmrsPathNode(tgtnid, TOP)]
        else:
            subpaths[axis] = list(
                _find_paths(xmrs, stepmap, tgtnid, flags,
                            max_distance-1, visited)
            )

    if subpaths:
        # beware of magic below:
        #   links maps a axis (like ARG1/NEQ) to a list of subpaths.
        #   This gets the product of subpaths for all axes, then remaps
        #   the axis to the appropriate subpaths. E.g. if links is like
        #   {':ARG1/NEQ>': [def], ':ARG2/NEQ>': [ghi, jkl]} then lds is like
        #   [{':ARG1/NEQ>': def, 'ARG2/NEQ>': ghi},
        #    {':ARG1/NEQ>': def, 'ARG2/NEQ>': jkl}]
        lds = map(
            lambda z: dict(zip(subpaths.keys(), z)),
            product(*subpaths.values())
        )
        for ld in lds:
            yield XmrsPathNode(start, symbol, context=ctext, links=ld)


# READING PATHS #############################################################

tokenizer = re.compile(
    # two kinds of strings: "double quoted", and 'open-single-quoted
    r'(?P<string>"[^"\\]*(?:\\.[^"\\]*)*"|\'[^ \\]*(?:\\.[^ \\]*)*)'
    # axes can be one of the following forms: :X/Y>, :X/Y:, <X/Y:
    r'|(?P<axis>:[^/]*/(?:EQ|NEQ|HEQ|H)[:>]|<[^/]*/(?:EQ|NEQ|HEQ|H):)'
    r'|(?P<symbol>[^\s#:><@=()\[\]&|]+)'  # non-breaking characters
    r'|(?P<nodeid>#\d+)'  # nodeids (e.g. #10003)
    r'|(?P<punc>[@=()\[\]&|])'  # meaningful punctuation
)

def read_path(path_string):
    toks = deque((mo.lastgroup, mo.group())
                 for mo in tokenizer.finditer(path_string))
    try:
        node = _read_node(toks)
    except IndexError:
        raise XmrsPathError('Unexpected termination for path: {}'
            .format(path_string))
    if node is None:
        raise XmrsPathError('Error reading path: {}'
            .format(path_string))
    elif toks:
        raise XmrsPathError('Unconsumed tokens: {}'
            .format(', '.join(tok[1] for tok in toks)))
    #path = XmrsPath.from_node(startnode)
    #return path
    return node

def _read_node(tokens):
    if not tokens or tokens[0][0] not in {'string', 'symbol', 'nodeid'}:
        return None
    # A node can be a pred, a nodeid, or both (in that order). This
    # means two 'if's, not 'if-else'.
    mtype, mtext = tokens.popleft()
    pred = nodeid = None
    if mtype in ('string', 'symbol'):
        if mtext == TOP or mtext == STAR:
            pred = mtext
        else:
            pred = Pred.stringpred(mtext)
        if tokens and tokens[0][0] == 'nodeid':
            mtype, mtext = tokens.popleft()
    if mtype == 'nodeid':
        nodeid = int(mtext[1:])  # get rid of the initial # character
    context = _read_context(tokens)
    links = _read_links(tokens)
    return XmrsPathNode(
        nodeid,
        pred,
        context=context,
        links=links
    )

def _read_context(tokens):
    if not tokens or tokens[0] != ('punc', '['):
        return None
    _, _ = tokens.popleft()  # this is the ('punc', '[')
    # context can be a varsort, an @attribute, or an axis
    context = {}
    for token in _read_conjunction(tokens):
        mtype, mtext = token
        if mtype == 'symbol':
            context['varsort'] = mtext
        elif token == ('punc', '@'):
            _, attr = tokens.popleft()
            assert tokens.popleft() == ('punc', '=')
            _, val = tokens.popleft()
            context['@{}'.format(attr)] = val
        elif mtype == 'axis':
            tgt = _read_node(tokens)
            context[mtext] = tgt
        else:
            raise XmrsPathError(
                'Invalid conjunct in context: {}'.format(mtext)
            )
    assert tokens.popleft() == ('punc', ']')
    return context


def _read_links(tokens):
    if not tokens or (tokens[0][0] != 'axis' and tokens[0][1] != '('):
        return None
    mtype, mtext = tokens.popleft()
    # it could be a single :axis
    if mtype == 'axis':
        return {mtext: _read_node(tokens)}
    # or (:many :axes)
    assert mtext == '('
    links = {}
    for token in _read_conjunction(tokens):
        mtype, mtext = token
        if mtype == 'axis':
            links[mtext] = _read_node(tokens)
        else:
            raise XmrsPathError('Invalid conjunct in axes: {}'.format(mtext))
    assert tokens.popleft() == ('punc', ')')
    return links


def _read_conjunction(tokens):
    yield tokens.popleft()
    while tokens[0] == ('punc', '&'):
        tokens.popleft()  # the & character
        yield tokens.popleft()


# # SEARCHING PATHS ###########################################################


def find_node(base, node=None, nodeid=None, pred=None, context=None):
    matches = []
    if node is None:
        node = XmrsPathNode(nodeid, pred, context=context)
    if _nodes_unifiable(base, node):
        matches.append(([], base))
    # there's no cycle detection below because paths are (supposedly) trees
    agenda = [([a], sp) for a, sp in base.links.items() if sp is not None]
    while agenda:
        axes, base = agenda.pop()
        if _nodes_unifiable(base, node):
            matches.append((axes, base))
        agenda.extend(
            (axes+[a], sp) for a, sp in base.links.items() if sp is not None
        )
    return matches


def _nodes_unifiable(n1, n2):
    if n1 is None or n2 is None:
        return True
    # nodeids same or one/both is None
    if not (n1.nodeid is None or
            n2.nodeid is None or
            n1.nodeid == n2.nodeid):
        return False
    # preds same or one/both is None or STAR
    if not (n1.pred in (None, STAR) or
            n2.pred in (None, STAR) or
            n1.pred == n2.pred):
        return False
    # context can be properties or subpaths
    for k, v2 in n2.context.items():
        if k[0] in (':', '<'):  # subpaths must be recursively unifiable
            if not _nodes_unifiable(n1.context.get(k), v2):
                return False
        else:  # properties just need to be equal
            v1 = n1.context.get(k)
            if not (v1 is None or v2 is None or v1 == v2):
                return False
    # links are just like context subpaths
    if not all(_nodes_unifiable(n1.links.get(axis), sp2)
                for axis, sp2 in n2.links.items()):
        return False
    return True



# def find_extents(node1, node2):
#     exts = []
#     for (base_axes, first_node) in find(node1, node2.pred):
#         try:
#             extset = extents(first_node, node2)
#             if extset:
#                 exts.append((base_axes, extset))
#         except XmrsPathError:
#             pass
#     return exts


# def extents(node1, node2):
#     if _nodes_informative(node1, node2):
#         return ([], node2)

#     assert node1.pred == node2.pred
#     exts = []
#     # if a constraint is violated, raise XmrsPathError
#     # if a constraint exists on node1 and node2, dive
#     # if one is on node1 but not node2, ignore
#     # if one is on node2 but not node1, return
#     for axis, tgt2 in node2.links.items():
#         if axis in node1.links:
#             tgt1 = node1.links[axis]
#             if tgt2 is None:
#                 continue
#             elif tgt1 is None:
#                 exts.append(([axis], tgt2))
#             elif _nodes_compatible(tgt1, tgt2):
#                 for axes, ext in extents(tgt1, tgt2):
#                     exts.append(([axis] + axes, ext))
#             else:
#                 raise XmrsPathError('Incompatible paths.')
#         else:
#             exts.append(([axis], tgt2))
#     return exts


# def _nodes_informative(n1, n2):
#     if

# def _nodes_compatible(n1, n2):
#     compatible = True
#     if n1.pred != n2.pred:
#         compatible = False
#     for k, v in n2.context.items():

#     return (
#         n1.pred == n2.pred and
#         all(n1.context.get(k, v) == v for k, v in n2.context.items()) and

#     )

# BUILDING XMRS#########################################################

def reify_xmrs(path):
    #from delphin.mrs import simpledmrs
    # if hasattr(path, 'start'):
    #     path = path.start
    if path.pred == TOP:
        assert len(path.links) == 1
        axis, path = list(path.links.items())[0]
    else:
        axis = ':/H>'  # just pretend there was a TOP:/H>
    if path is None:
        return []
    for upath, _, _ in _unique_paths(path, defaultdict(set), 10000):
        m = _reify_xmrs(upath, top_axis=axis)
        if m.is_well_formed():
            yield m
            #print(simpledmrs.dumps_one(m, pretty_print=True))


def _unique_paths(path, nidmap, nextnid):
    if path is None:
        yield (path, nidmap, nextnid)
        return
    # first get possibilities for the current node
    node_repr = format(path, depth=0, flags=PRED|CONTEXT)

    # if already has nodeid, use it; otherwise create or use from nidmap
    if path.nodeid is None:
        nids = [nextnid]
        # only consider existing nids if they aren't quantifiers because
        # we expect to see many quantifiers but they are all unique
        if not path.pred.is_quantifier():
            nids += list(nidmap.get(node_repr, []))
        nextnid += 1
    else:
        nids = [path.nodeid]
    alts = []
    for nid in nids:
        alts.append((
            _new_node(path, nid),
            _new_nidmap(nidmap, node_repr, nid),
            nextnid
        ))
    # then for each alternative, find possible descendants
    agenda = list(path.links.items())
    while agenda:
        _alts = []
        axis, tgt = agenda.pop()
        for node, nm, nn in alts:
            for subpath, _nm, _nn in _unique_paths(tgt, nm, nn):
                n = copy(node)
                n.links[axis] = subpath
                _alts.append((n, _nm, _nn))
        alts = _alts
    for alt in alts:
        yield alt


def _new_node(node, nid=None):
    new_node = copy(node, depth=0)
    if nid is not None:
        new_node.nodeid = nid
    return new_node


def _new_nidmap(nidmap, node_repr, nid):
    nm = defaultdict(set, {k: v.copy() for k, v in nidmap.items()})
    nm[node_repr].add(nid)
    return nm


def _reify_xmrs(path, top_axis=None):
    nodes = {}
    links = []
    agenda = [(0, top_axis or ':/H>', path)]
    while agenda:
        srcnid, axis, tgt = agenda.pop()
        if tgt is None:
            continue
        # add link to tgt
        rargname, post = axis.strip(':<>').split('/')
        if axis.startswith('<'):
            links.append(Link(tgt.nodeid, srcnid, rargname or None, post))
        elif axis.endswith('>'):
            links.append(Link(srcnid, tgt.nodeid, rargname or None, post))
        elif axis == ':/EQ:':
            links.append(Link(srcnid, tgt.nodeid, None, 'EQ'))
        else:
            raise XmrsPathError('Invalid axis: {}'.format(axis))
        # add node if necessary (note, currently does not update pred
        # or sortinfo if encountered twice)
        if tgt.nodeid not in nodes:
            sortinfo = dict(
                [('cvarsort', tgt.context.get('varsort', 'u'))] +
                [(k.lstrip('@', 1), v)
                 for k, v in tgt.context.items() if k.startswith('@')]
            )
            nodes[tgt.nodeid] = Node(tgt.nodeid, tgt.pred, sortinfo=sortinfo)
        # add new agenda for tgt
        for axis, next_tgt in tgt.links.items():
            agenda.append((tgt.nodeid, axis, next_tgt))
    return Dmrs(list(nodes.values()), links)
