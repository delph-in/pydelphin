"""
Classes and functions for path exploration on semantic graphs.
"""

#import pdb
import re
import warnings
from collections import deque, defaultdict
from itertools import product

from .components import (Pred, links, var_sort)
from .util import powerset
from .config import IVARG_ROLE
from delphin.exceptions import XmrsError
# for rebuilding Xmrs from paths
from delphin.mrs import Node, Link, Pred, Dmrs

TOP = 'TOP'
STAR = '*'

# flags
NODEID = NID = 1            # pred#NID... or #NID...
PRED = P = 2                # pred or "pred" or 'pred
VARSORT = VS = 4            # pred[e], pred[x], etc.
VARPROPS = VP = 8           # pred[@PROP=val]
OUTAXES = OUT = 16          # pred:ARG1/NEQ>
INAXES = IN = 32            # pred<ARG1/EQ:
UNDIRECTEDAXES = UND = 64   # pred:/EQ:
SUBPATHS = SP = 128         # pred:ARG1/NEQ>pred2
CARG = C = 256              # pred:CARG>"value"
BALANCED = B = 512

CONTEXT = VS | VP | SP
ALLAXES = OUT | IN | UND
DEFAULT = P | VS | VP | OUT | IN | SP
ALL = NID | P | VS | VP | OUT | IN | UND | SP

class XmrsPathError(XmrsError): pass


# GRAPH WALKING ########################################################

def axis_sort(axis):
    return (
        not axis[-1] == '>',  # forward links first
        not axis[0] == '<',  # then backward, then undirected
        not (len(axis) >= 5 and axis[1:4] == 'LBL'),  # LBL before other args
        (len(axis) >= 6 and axis[1:5] == 'BODY'),  # BODY last
        axis[1:]  # otherwise alphabtical
    )


def step_sort(step):
    nodeid, axis = step
    return tuple(
        list(axis_sort(axis)) + [nodeid]
    )


def walk(xmrs, start=0, method='headed', sort_key=step_sort):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))

    if not (start == 0 or xmrs.pred(start)):
        raise XmrsPathError('Start nodeid not in Xmrs graph.')

    linkdict = _build_linkdict(xmrs)
    for step in _walk(start, linkdict, set(), method, sort_key):
        yield step


def _walk(nodeid, linkdict, visited, method, sort_key):
    if nodeid in visited:
        return
    visited.add(nodeid)

    local_links = linkdict.get(nodeid, [])
    steps = sorted(
        filter(_axis_filter(method), local_links),
        key=sort_key
    )
    for tgtnid, axis in steps:
        # if this undirected link was already traversed in the other
        # direction, just yield this step but don't recurse
        if axis == ':/EQ:' and tgtnid in visited:
            #yield (nodeid, tgtnid, axis)
            continue
        yield (nodeid, tgtnid, axis)
        for step in _walk(tgtnid, linkdict, visited, method, sort_key):
            yield step


def _build_linkdict(xmrs):
    ld = defaultdict(list)
    for link in links(xmrs):
        axis = '{}/{}'.format(link.rargname or '', link.post)
        if link_is_directed(link):
            ld[link.start].append((link.end, ':{}>'.format(axis)))
            ld[link.end].append((link.start, '<{}:'.format(axis)))
        else:
            # pretend they are directed
            #ld[link.end]['<{}:'.format(axis)] = link.start
            ld[link.start].append((link.end, ':{}:'.format(axis)))
            ld[link.end].append((link.start, ':{}:'.format(axis)))
    return ld


def _axis_filter(method):
    # top-down: :X/Y> or :X/Y: (the latter only if added)
    def axis_filter(step):
        nid, axis = step
        if method == 'headed' and headed(axis) or \
           method == 'top-down' and axis.startswith(':') or \
           method == 'bottom-up' and axis.endswith(':'):
            return True
        return False
    return axis_filter


def link_is_directed(link):
    return bool(link.rargname) or link.post != 'EQ'


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

    __slots__ = ('nodeid', 'pred', 'context', 'links', '_overlapping_links',
                 '_depth', '_order')

    def __init__(self, nodeid, pred, context=None, links=None):
        self.nodeid = nodeid
        self.pred = pred
        self.context = dict(context or [])
        self.links = dict(links or [])
        self._overlapping_links = {}  # {overlapping_axis: orig_axis, ...}
        self._depth = (
            max([-1] +
                [x._depth for x in self.links.values() if x is not None]) +
            1
        )
        self._order = (
            sum(x._order for x in self.links.values() if x is not None) +
            1
        )

    def __getitem__(self, key):
        return self.links[key]

    def __iter__(self):
        return iter(self.links.items())

    def __len__(self):
        return self._depth

    def update(self, other):
        self.nodeid = other.nodeid or self.nodeid
        self.pred = other.pred or self.pred
        self.context.update(other.context or [])
        for axis, tgt in other.links.items():
            if not self.links.get(axis):
                self.links[axis] = tgt
            else:
                self[axis].update(tgt)

    def depth(self):
        return self._depth

    def order(self):
        return self._order


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


# class XmrsPath(XmrsPathNode):

#     def __init__(self, nodeid, pred, context=None, links=None):
#         XmrsPathNode.__init__(self, nodeid, pred, context, links)
#         self.calculate_metrics()

#     @classmethod
#     def from_node(cls, node):
#         return cls(node.nodeid, node.pred, node.context, node.links)

#     def calculate_metrics(self):
#         self._distance = {}
#         self._depth = {}
#         self._preds = {}
#         self._calculate_metrics(self, 0, 0)

#     def _calculate_metrics(self, curnode, depth, distance):
#         if curnode is None:
#             return
#         # add pred index
#         try:
#             self._preds[curnode.pred].append(curnode)
#         except KeyError:
#             self._preds[curnode.pred] = []
#             self._preds[curnode.pred].append(curnode)
#         _id = id(curnode)
#         # we may re-update if we're on a shorter path
#         updated = False
#         if _id not in self._distance or distance < self._distance[_id]:
#             self._distance[_id] = distance
#             updated = True
#         if _id not in self._depth or abs(depth) < abs(self._depth[_id]):
#             self._depth[_id] = depth
#             updated = True
#         if not updated:
#             return
#         for link in curnode.links:
#             if link.endswith('>'):
#                 self._calculate_metrics(curnode[link], depth+1, distance+1)
#             elif link.startswith('<'):
#                 self._calculate_metrics(curnode[link], depth-1, distance+1)
#             else:
#                 self._calculate_metrics(curnode[link], depth, distance+1)

#     def distance(self, node=None):
#         if node is None:
#             return max(self._distance.values())
#         else:
#             return self._distance[id(node)]

#     def depth(self, node=None, direction=max):
#         if node is None:
#             return direction(self._depth.values())
#         return self._depth[id(node)]

#     def select(self, pred):
#         return self._preds.get(pred, [])

#     # def extend(self, extents, base_axes=None):
#     #     if base_axes is None:
#     #         base_axes = []
#     #     base = self.follow(base_axes)
#     #     base.extend(extents)
#     #     self.calculate_metrics()


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
            if tgt is None:
                if _valid_axis(axis, flags):
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
    if depth != 0:
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
            elif k[0] == '@':
                if (flags & VARPROPS):
                    contexts.append('{}={}'.format(k, v))
            elif k[0] in (':', '<'):
                if v is not None and (flags & SUBPATHS):
                    v = format(v, sort_key, depth-1, flags)
                elif _valid_axis(k, flags):
                    v = ''
                else:
                    continue
                contexts.append('{}{}'.format(k, v))
            else:
                raise XmrsPathError('Invalid context key: {}'.format(k))
        if contexts:
            context = '[{}]'.format(' & '.join(contexts))
    return context


def _format_subpath(node, sort_key, depth, flags):
    links = []
    axislist = _prepare_axes(node, sort_key)
    for axis, tgt in axislist:
        if tgt is not None and (flags & SUBPATHS):
            tgt = format(tgt, sort_key, depth, flags)
        elif _valid_axis(axis, flags):
            tgt = ''
        else:
            continue
        links.append('{}{}'.format(axis, tgt))
    if len(links) > 1:
        subpath = '({})'.format(' & '.join(links))
    else:
        subpath = ''.join(links)  # possibly just ''
    return subpath


def _prepare_axes(node, sort_key):
    """
    Sort axes and combine those that point to the same target and go
    in the same direction.
    """
    links = node.links
    o_links = node._overlapping_links
    overlap = {ax2 for ax in links for ax2 in o_links.get(ax, [])}
    axes = []
    for axis in sorted(links.keys(), key=sort_key):
        if axis in overlap: continue
        tgt = links[axis]
        if axis in o_links:
            s, e = axis[0], axis[-1]
            axis = '%s%s%s' % (
                s, '&'.join(a[1:-1] for a in [axis] + o_links[axis]), e
            )
        axes.append((axis, tgt))
    return axes


def _context_sort(k):
    return (k != 'varsort', k[0] in (':', '<'), k)


# FINDING PATHS #############################################################

def find_paths(
        xmrs,
        nodeids=None,
        method='top-down',
        flags=DEFAULT,
        max_distance=-1,
        subpath_select=list):
    warnings.warn('find_paths() is deprecated; use explore()',
                  DeprecationWarning)
    return explore(xmrs, nodeids, method, flags, max_distance, subpath_select)


def explore(
        xmrs,
        nodeids=None,
        method='top-down',
        flags=DEFAULT,
        max_distance=-1,
        subpath_select=list):
    if nodeids is None: nodeids = [0] + xmrs._nodeids  # 0 for TOP
    stepmap = defaultdict(lambda: defaultdict(set))
    for startnid in nodeids:
        if startnid in stepmap:
            continue  # start node already done
        for start, end, axis in walk(xmrs, start=startnid, method=method):
            stepmap[start][end].add(axis)
            # if axis in stepmap.get(start, {}):
            #     continue  # current node already done
            # stepmap[start][axis] = end
    for nodeid in nodeids:
        for node in _explore(
                xmrs, stepmap, nodeid, flags,
                max_distance, subpath_select, set()):
            #yield XmrsPath.from_node(node)
            yield node


def _explore(
        xmrs,
        stepmap,
        start,
        flags,
        max_distance,
        subpath_select,
        visited):
    if start in visited:
        return
    visited = visited.union([start])
    ctext = None
    if start == 0:
        symbol = TOP
    else:
        symbol = xmrs.pred(start)
        if (flags & CONTEXT):
            ctext = {}
            # it's not guaranteed that an EP has an intrinsic variable
            if IVARG_ROLE in xmrs.args(start):
                iv = xmrs.args(start)[IVARG_ROLE]
                varsort = var_sort(iv)
                ctext['varsort'] = varsort
                props = xmrs.properties(iv)
                ctext.update([
                    ('@{}'.format(k), v)
                    for k, v in props.items()
                ])
    steps = stepmap.get(start, {})  # this is {end_nodeid: set(axes), ...}
    # remove :/EQ: if necessary and generate mapping for overlapping axes
    overlap = {}
    for end, axes in steps.items():
        if (':/EQ:' in axes and
                (not (flags & UNDIRECTEDAXES) or
                 (end in visited and ':/EQ:' in stepmap[end].get(start, [])))):
            axes.difference_update([':/EQ:'])
        if len(axes) > 1:
            # don't sort if this significantly hurts performance
            axes = sorted(axes, key=axis_sort)
            s, e = axes[0][0], axes[0][-1]  # axis direction characters
            overlap[axes[0]] = [
                ax for ax in axes[1:] if ax[0] == s and ax[-1] == e
            ]

    # exclude TOP from being its own path node
    if start != 0:
        n = XmrsPathNode(
            start,
            symbol,
            context=ctext,
            links={axis: None for axes in steps.values() for axis in axes}
        )
        n._overlapping_links = overlap
        yield n

    # keep tuples of axes instead of mapping each unique axis. This is
    # for things like coordination where more than one axis point to the
    # same thing, and we don't want to enumerate all possibilities.
    subpaths = {}
    for tgtnid, axes in steps.items():
        if tgtnid == 0:
            # assume only one axis going to TOP (can there be more than 1?)
            axis = next(iter(axes))
            subpaths[(axis,)] = [XmrsPathNode(tgtnid, TOP)]
        elif (flags & SUBPATHS) and max_distance != 0:
            if not axes:  # maybe an :/EQ: was pruned and nothing remained
                continue
            sps = subpath_select(list(
                _explore(xmrs, stepmap, tgtnid, flags,
                            max_distance-1, subpath_select, visited)
            ))
            if not (flags & BALANCED):
                sps.append(None)
            subpaths[tuple(axes)] = sps

    if subpaths:
        # beware of magic below:
        #   links maps a tuple of axes (usually just one axis, like
        #   (ARG1/NEQ,)) to a list of subpaths.
        #   This gets the product of subpaths for all axes, then remaps
        #   axis tuples to the appropriate subpaths. E.g. if subpaths is
        #     {(':ARG1/NEQ>',): [def],
        #      (':ARG2/NEQ>',':ARG3/EQ>'): [ghi, jkl]}
        #   then alts is
        #     [{(':ARG1/NEQ>',): def, ('ARG2/NEQ>', ':ARG3/EQ>'): ghi},
        #      {(':ARG1/NEQ>',): def, ('ARG2/NEQ>', ':ARG3/EQ>'): jkl}]
        alts = list(map(
            lambda z: dict(zip(subpaths.keys(), z)),
            product(*subpaths.values())
        ))
        # now enumerate the tupled axes
        for alt in alts:
            ld = dict((a, tgt) for axes, tgt in alt.items() for a in axes)
            # don't output all null axes (already done above)
            if set(ld.values()) != {None}:
                n = XmrsPathNode(start, symbol, context=ctext, links=ld)
                n._overlapping_links = overlap
                yield n


# READING PATHS #############################################################

tokenizer = re.compile(
    # two kinds of strings: "double quoted", and 'open-single-quoted
    r'(?P<string>"[^"\\]*(?:\\.[^"\\]*)*"|\'[^ \\]*(?:\\.[^ \\]*)*)'
    # axes should be like :X/Y>, <X/Y:, :X/Y:, :X/Y&A/B>, etc.
    r'|(?P<axis>[<:][^/]*/(?:[HN]?EQ|H)(?:&[^/]*/(?:[HN]?EQ|H))*[:>])'
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
            start, end = mtext[0], mtext[-1]
            axes = mtext[1:-1].split('&')
            for ax in axes:
                ax = '%s%s%s' % (start, ax.strip(), end)
                context[ax] = tgt
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
            tgt = _read_node(tokens)
            start, end = mtext[0], mtext[-1]
            axes = mtext[1:-1].split('&')
            for ax in axes:
                ax = '%s%s%s' % (start, ax.strip(), end)
                links[ax] = tgt
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


def match(pattern, p, flags=DEFAULT):
    if (flags & NODEID) and (pattern.nodeid != p.nodeid):
        return False
    if (flags & PRED):
        p1 = pattern.pred
        p2 = p.pred
        if not (p1 == STAR or p2 == STAR or p1 == p2):
            return False
    if (flags & CONTEXT):
        c1 = pattern.context
        c2 = p.context
        check_sp = flags & SUBPATHS
        check_vs = flags & VARSORT
        check_vp = flags & VARPROPS
        for k, a in c1.items():
            if k[0] in (':', '<') and check_sp:
                b = c2.get(k)
                if not (a is None or b is None or match(a, b)):
                    return False
            elif (k == 'varsort' and check_vs) or check_vp:
                if c2.get(k, a) != a:
                    return False
    if (flags & SUBPATHS):
        for axis, pattern_ in pattern.links.items():
            p_ = p.links.get(axis)
            if not (pattern_ is None or p_ is None or match(pattern_, p_)):
                return False
    return True


def subpaths(p):
    all_sps = []
    sps = list(_subpaths(p))
    sps = sps[1:]  # the first subpath is the same as the original
    return sps


def _subpaths(p):
    if p is None:
        return
    sps = {ax: list(_subpaths(tgt)) + [None] for ax, tgt in p.links.items()}
    # this fancy bit is the same as in _explore()
    alts = list(map(
        lambda z: dict(zip(sps.keys(), z)),
        product(*sps.values())
    ))
    for alt in alts:
        ld = dict((axis, tgt) for axis, tgt in alt.items())
        n = XmrsPathNode(p.nodeid, p.pred, context=p.context, links=ld)
        n._overlapping_links = p._overlapping_links
        yield n


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
        return
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
                [('cvarsort', tgt.context.get('varsort') or 'u')] +
                [(k.lstrip('@'), v)
                 for k, v in tgt.context.items() if k.startswith('@')]
            )
            nodes[tgt.nodeid] = Node(tgt.nodeid, tgt.pred, sortinfo=sortinfo)
        # add new agenda for tgt
        for axis, next_tgt in tgt.links.items():
            agenda.append((tgt.nodeid, axis, next_tgt))
    return Dmrs(list(nodes.values()), links)
