import re
from collections import deque, defaultdict
from itertools import product
from .components import Pred
from .util import powerset
from delphin._exceptions import XmrsError

class XmrsPathError(XmrsError): pass

TOP = 'TOP'

# Something like this:
#
# Start              = OrPathExpr
# OrPathExpr         = AndPathExpr ("|" AndPathExpr)*
# AndPathExpr        = PathExpr ("&" PathExpr)*
# PathExpr           = Path (ExprOp Value)?
# ExprOp             = "=" | "is"
# Value              = Path | String | "_"
# Path               = PathGroup | TopPath | EPPath
# PathGroup          = "(" OrPathExpr ")"
# TopPath            = TopVar (PathOp EPPath)?
# TopVar             = "LTOP" | "INDEX"
# PathOp             = "/" | "%" | "^" | "~"
# EPPath             = EP EPCondition? EPComponents?
# EP                 = Pred | "#" NodeIdOrAnchor | "*"
# NodeIdOrAnchor     = NodeId | Anchor
# EPCondition        = "[" OrEPComponentExpr "]"
# EPComponents       = EPComponentGroup | EPComponent
# EPComponentGroup   = "(" OrEPComponentExpr ")"
# OrEPComponentExpr  = AndEPComponentExpr ("|" AndEPComponentExpr)*
# AndEPComponentExpr = EPComponentExpr ("&" EPComponentExpr)*
# EPComponentExpr    = (EPComponent | Path) (ExprOp Value)?
# EPComponent        = ArgPath | Property
# ArgPath            = ":" ArgName (PathOp (EPPath | PathGroup))?
# ArgName            = "*" | String
# Property           = "@" PropName
# PropName           = "*" | String

# also empty input; check separately
_path_end_tokens = set([')', ']', '|', '&'])
_top_vars = set(['LTOP', 'INDEX'])
_expression_operators = set(['=', 'is'])
_non_pred_toks = set([':', '/', '%', '^', '~', '@', ')',
                      '[', ']', '=', '&', '|'])  # '('




def tokenize(path):
    """Split the path into tokens."""
    return tokenizer.findall(path)


def walk(xmrs, path):
    # for now path is space separated
    path_tokens = path.split()


def traverse(xmrs, path):
    steps = deque(tokenize(path))
    objs = _traverse_disjunction(xmrs, xmrs, steps, _traverse_pathexpr)
    if steps:
        raise Exception('Unconsumed MrsPath steps: {}'.format(''.join(steps)))
    return objs


# _traverse_disjunction and _traverse_conjunction are general-purpose,
# and thus need a traverser argument, which says what they are
# disjoining and conjoining
def _traverse_disjunction(xmrs, obj, steps, traverser, context=None):
    objs = _traverse_conjunction(xmrs, obj, steps, traverser, context)
    while steps and steps[0] == '|':
        steps.popleft()  # get rid of '|'
        objs.extend(_traverse_conjunction(xmrs, obj, steps, traverser,
                                          context))
    return objs


def _traverse_conjunction(xmrs, obj, steps, traverser, context=None):
    objs = traverser(xmrs, obj, steps, context)
    # &-ops can fail early, since all must evaluate to True to be
    # used, but we can't short-circuit conjunction unless we know how
    # many steps to remove from the queue, so just parse them for now
    while steps and steps[0] == '&':
        steps.popleft()  # get rid of '&'
        objs2 = traverser(xmrs, obj, steps, context)
        if objs and objs2:
            objs.extend(objs2)
        else:
            objs = []
    return objs


def _traverse_pathexpr(xmrs, obj, steps, context=None):
    # PathExpr = Path (ExprOp Value)?
    objs = _traverse_path(xmrs, obj, steps, context)
    if steps and steps[0] in _expression_operators:
        values = _traverse_value(xmrs, obj, steps, context)
        if step == '=':
            return objs == values
        elif step == 'is':
            raise NotImplementedError
    return objs


def _traverse_path(xmrs, obj, steps, context=None):
    # Path = PathGroup | TopPath | EPPath
    if steps[0] == '(':
        return _traverse_pathgroup(xmrs, obj, steps, context=obj)
    elif steps[0].upper() in _top_vars:
        return _traverse_toppath(xmrs, obj, steps, context)
    else:
        return _traverse_eppath(xmrs, obj, steps, context)


def _traverse_pathgroup(xmrs, obj, steps, context=None):
    # PathGroup = "(" OrPathExpr ")"
    steps.popleft()  # remove '('
    objs = _traverse_disjunction(xmrs, obj, steps, _traverse_pathexpr,
                                 context)
    steps.popleft()  # remove ')'


def _traverse_toppath(xmrs, obj, steps, context=None):
    # TopPath = TopVar (PathOp EPPath)?
    # TopVar = "LTOP" | "INDEX"
    step = steps.popleft().upper()
    if step == 'LTOP':
        raise NotImplementedError
    elif step == 'INDEX':
        raise NotImplementedError


def _traverse_eppath(xmrs, obj, steps, context=None):
    # EPPath = EP EPCondition? EPComponents?
    # EP = Pred | "#" NodeIdOrAnchor | "*"
    # NodeIdOrAnchor = NodeId | Anchor
    eps = _traverse_ep(xmrs, obj, steps, context)

    if steps and step[0] == '[':
        eps = list(filter())
    if steps and step[0] == '(':
        pass


def _traverse_ep(xmrs, obj, steps, context=None):
    step = steps.popleft()
    if step == '*':
        eps = xmrs.nodes
    elif step == '#':
        nid = steps.popleft()
        eps = xmrs.select_nodes(nodeid=nid)
    elif Pred.is_valid_pred_string(step, suffix_required=False):
        eps = xmrs.select_nodes(pred=step)
    else:
        raise Exception("Invalid ep: {}".format(''.join([step] + steps)))


def _traverse_arg(xmrs, obj, steps):
    pass
    if step in (')', ']'):
        pass
        #    return objs
        #    elif step == '[':
        #    if traverse(xmrs, curobj, steps):
        #        objs.append(curobj)
    elif step == ':':
        member = steps[1]
        obj = obj.get_member()
    elif step == '/':
        pass
    elif step == '%':
        pass
    elif step == '^':
        pass
    elif step == '~':
        pass
    elif step == '':
        pass


def find(xmrs, path):
    pass

# GENERATING PATHS #########################################################


class XmrsPath(object):

    __slots__ = ('start', '_depth', '_distance')

    def __init__(self, startnode):
        self.start = startnode
        self.calculate_metrics()

    def calculate_metrics(self):
        self._distance = {}
        self._depth = {}
        self._calculate_metrics(self.start, 0, 0)

    def _calculate_metrics(self, curnode, depth, distance):
        if curnode is None:
            return
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

class XmrsPathNode(object):

    __slots__ = ('nodeid', 'pred', 'links')

    def __init__(self, nodeid, pred, links=None):
        self.nodeid = nodeid
        self.pred = pred
        self.links = dict(links or [])

    def __getitem__(self, key):
        return self.links[key]

    def __iter__(self):
        return iter(self.links.items())


def get_nodeids(path):
    yield path.nodeid
    for link, path_node in path:
        if path_node is None:
            continue
        for nid in get_nodeids(path_node):
            yield nid


def get_preds(path):
    yield path.pred
    for link, path_node in path:
        if path_node is None:
            continue
        for pred in get_preds(path_node):
            yield pred


def link_is_directed(link):
    return bool(link.argname) or link.post != 'EQ'


def headed(connector):
    # quantifiers and X/EQ links are not the heads of their subgraphs
    return not (connector == ':RSTR/H>' or connector.endswith('/EQ>'))


def connector_sort(connector):
    return (
        not connector.endswith('>'),  # forward links first
        not connector.startswith('<'),  # then backward, then undirected
        not connector[1:].startswith('LBL'),  # LBL before other args
        connector[1:].startswith('BODY'),  # BODY last
        connector[1:]  # otherwise alphabetical
    )

def format(node, sort_key=connector_sort, trailing_connectors='always'):
    if isinstance(node, XmrsPath):
        node = node.start
    return _format(
        node, sort_key=sort_key, trailing_connectors=trailing_connectors
    )

def _format(node, sort_key=connector_sort, trailing_connectors='always'):
    if node is None:
        return ''
    #if node.nodeid is not None:
    #    symbol = '#{}'.format(node.nodeid)
    if node.pred is not None:
        symbol = str(node.pred)
    else:
        symbol = '*'
    links = []
    connectors = node.links.keys()
    if sort_key:
        connectors = sorted(connectors, key=sort_key)
    for conn in connectors:
        tgt = node.links[conn]
        if (tgt or
            trailing_connectors == 'always' or
            (trailing_connectors == 'forward' and conn.endswith('>')) or
            (trailing_connectors == 'backward' and conn.startswith('<'))):

            links.append(
                '{}{}'.format(
                    conn,
                    _format(
                        tgt,
                        sort_key=sort_key,
                        trailing_connectors=trailing_connectors
                    )
                )
            )
    if len(links) > 1:
        subpath = '({})'.format(' & '.join(links))
    else:
        subpath = ''.join(links)  # possibly just ''
    return '{}{}'.format(symbol, subpath)


def find_paths(
        xmrs,
        nodeids=None,
        method='top-down',
        allow_eq=False,
        max_distance=-1):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))
    if nodeids is None: nodeids = [0] + xmrs.nodeids  # 0 for TOP
    links = _build_linkdict(xmrs, allow_eq)

    paths = defaultdict(list)
    for nid in nodeids:
        if nid in paths: continue  # maybe already visited in find_paths_from_node
        for path in find_paths_from_node(
                xmrs, nid, method=method, allow_eq=allow_eq,
                max_distance=max_distance, links=links, seen=set()):
            paths[path.start.nodeid].append(path)

    for nid in nodeids:
        for path in sorted(paths.get(nid, []), key=lambda p: p.distance()):
            yield path

def _build_linkdict(xmrs, allow_eq):
    links = defaultdict(dict)
    for link in xmrs.links:
        connector = '{}/{}'.format(link.argname or '', link.post)
        if link_is_directed(link):
            links[link.start][':{}>'.format(connector)] = link.end
            links[link.end]['<{}:'.format(connector)] = link.start
        elif allow_eq:
            links[link.start][':{}:'.format(connector)] = link.end
            links[link.end][':{}:'.format(connector)] = link.start
    return links

def find_paths_from_node(
        xmrs,
        nodeid,
        method='top-down',
        allow_eq=False,
        max_distance=-1,
        links=None,
        seen=None):
    if method not in ('top-down', 'bottom-up', 'headed'):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))
    if links is None: links = _build_linkdict(xmrs)
    if seen is None: seen = set()
    if nodeid in seen or max_distance == 0: return None

    symbol = TOP if nodeid == 0 else xmrs.get_pred(nodeid)
    local_links = links.get(nodeid, {})
    connectors = _get_connectors(method, local_links)
    # first just use the unfilled connectors
    yield XmrsPath(XmrsPathNode(nodeid, symbol, links=connectors))

    if connectors:
        links = {}
        for connector in connectors:
            links[connector] = list(map(
                lambda p: p.start,
                list(find_paths_from_node(
                    xmrs, local_links[connector], method=method,
                    allow_eq=allow_eq, max_distance=max_distance-1,
                    links=links, seen=seen
                ))
            ))
        # beware of magic below:
        #   links maps a connector (like ARG1/NEQ) to a list of subpaths.
        #   This gets the product of subpaths for all connectors, then remaps
        #   the connector to the appropriate subpaths. E.g. if links is like
        #   {':ARG1/NEQ>': [def], ':ARG2/NEQ>': [ghi, jkl]} then lds is like
        #   [{':ARG1/NEQ>': def, 'ARG2/NEQ>': ghi},
        #    {':ARG1/NEQ>': def, 'ARG2/NEQ>': jkl}]
        lds = map(
            lambda z: dict(zip(links.keys(), z)),
            product(*links.values())
        )
        for ld in lds:
            yield XmrsPath(XmrsPathNode(nodeid, symbol, links=ld))

def _get_connectors(method, links):
    # top-down: :X/Y> or :X/Y: (the latter only if added)
    if method == 'top-down':
        return dict((c, None) for c in links if c.startswith(':'))
    elif method == 'bottom-up':
        return dict((c, None) for c in links if c.endswith(':'))
    elif method == 'headed':
        return dict((c, None) for c in links if headed(c))


## READING PATHS

tokenizer = re.compile(
    r'(?P<dq_string>"[^"\\]*(?:\\.[^"\\]*)*")'  # quoted strings
    r"|(?P<sq_string>'[^ \\]*(?:\\.[^ \\]*)*)"  # single-quoted 'strings
    r'|(?P<fwd_connector>:[^/]*/(?:EQ|NEQ|HEQ|H)>)'  # :X/Y> connector
    r'|(?P<bak_connector><[^/]*/(?:EQ|NEQ|HEQ|H):)'  # <X/Y: connector
    r'|(?P<und_connector>:[^/]*/(?:EQ|NEQ|HEQ|H):)'  # :X/Y: connector
    r'|(?P<symbol>[^\s*:/><@()\[\]=&|]+)'  # non-breaking characters
    r'|(?P<punc>[*()&|])'  # meaningful punctuation
)

def read_path(path_string):
    toks = deque((mo.lastgroup, mo.group())
                 for mo in tokenizer.finditer(path_string))
    try:
        startnode = _read_node(toks)
    except IndexError:
        raise XmrsPathError('Unexpected termination for path: {}'
            .format(path_string))
    if startnode is None:
        raise XmrsPathError('Error reading path: {}'
            .format(path_string))
    elif toks:
        raise XmrsPathError('Unconsumed tokens: {}'
            .format(', '.join(tok[1] for tok in toks)))
    path = XmrsPath(startnode)
    return path

def _read_node(tokens):
    if not tokens: return None
    mtype, mtext = tokens.popleft()
    if mtype in ('dq_string', 'sq_string', 'symbol'):
        links = _read_links(tokens)
        return XmrsPathNode(
            None,
            Pred.stringpred(mtext),
            links
        )
    else:
        tokens.appendleft((mtype, mtext))  # put it back
    return None  # current position isn't a path node

def _read_links(tokens):
    if not tokens: return None
    mtype, mtext = tokens.popleft()
    if mtype in ('fwd_connector', 'bak_connector', 'und_connector'):
        return {mtext: _read_node(tokens)}
    elif mtext == '(':
        links = {}
        mtype, mtext = tokens.popleft()
        while mtext != ')':
            links[mtext] = _read_node(tokens)
            mtype, mtext = tokens.popleft()
            if mtext in ('&', '|'):
                mtype, mtext = tokens.popleft()
            elif mtext != ')':
                raise XmrsPathError('Unexpected token: {}'.format(mtext))
        return links
    else:
        tokens.appendleft((mtype, mtext))  # put it back
    return None  # not a link
