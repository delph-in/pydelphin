import re
from collections import deque, defaultdict
from itertools import product
from .components import Pred
from .util import powerset
from delphin._exceptions import XmrsError

class XmrsPathError(XmrsError): pass

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


class XmrsPathNode(object):

    __slots__ = ('nodeid', 'pred', 'links', 'depth', 'distance')

    def __init__(self, nodeid, pred, links=None, depth=None, distance=None):
        self.nodeid = nodeid
        self.pred = pred
        self.links = dict(links or [])
        self.depth = depth
        self.distance = distance

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
    return bool(link.argname)


def headed(connector):
    # quantifiers and X/EQ links are not the heads of their subgraphs
    return not (connector == 'RSTR/H' or connector.endswith('/EQ'))


def connector_sort(connector):
    return (
        not connector.endswith('>'),  # forward links first
        not connector.startswith('<'),  # then backward, then undirected
        not connector[1:].startswith('LBL'),  # LBL before other args
        connector[1:].startswith('BODY'),  # BODY last
        connector[1:]  # otherwise alphabetical
    )


def format_path(path,
                sort_connectors=connector_sort,
                trailing_connectors='always'):
    if path is None:
        return ''
    links = []
    connectors = path.links.keys()
    if sort_connectors:
        connectors = sorted(connectors, key=sort_connectors)
    for conn in connectors:
        tgt = path.links[conn]
        if (tgt or
            trailing_connectors == 'always' or
            (trailing_connectors == 'forward' and conn.endswith('>')) or
            (trailing_connectors == 'backward' and conn.startswith('<'))):

            links.append(
                '{}{}'.format(conn, format_path(tgt))
            )
    if len(links) > 1:
        subpath = '({})'.format(' & '.join(links))
    else:
        subpath = ''.join(links)  # possibly just ''
    return '{}{}'.format(path.pred.string, subpath)

def find_paths(xmrs, method="directed", allow_eq=False):
    if method not in ("directed", "headed"):
        raise XmrsPathError("Invalid path-finding method: {}".format(method))
    fwdlinks = defaultdict(dict)
    baklinks = defaultdict(dict)
    for link in xmrs.links:
        if link_is_directed(link) or allow_eq:
            connector = '{}/{}'.format(link.argname or '', link.post)
            fwdlinks[link.start][connector] = link
            baklinks[link.end][connector] = link
    paths = defaultdict(list)
    for nid in xmrs.nodeids:
        if nid in paths: continue  # maybe already visited in _find_paths
        for path in _find_paths(xmrs, nid, method,
                                fwdlinks, baklinks, set()):
            paths[path.nodeid].append(path)
    for nid in xmrs.nodeids:
        for path in sorted(paths.get(nid, []), key=lambda p: p.depth):
            yield path

def _find_paths(xmrs, nodeid, method, fwdlinks, baklinks, seen, depth=1):
    if nodeid in seen:
        return None
    seen.add(nodeid)

    curpath = XmrsPathNode(
        nodeid,
        xmrs._graph.node[nodeid]['pred'],
        links=dict((c, None) for c in fwdlinks.get(nodeid, {})),
        depth=1
    )
    yield curpath

    connections = []
    connections = list(fwdlinks[nodeid].keys())
    if method == "headed":
        connections = list(filter(headed, connections))
        connections.extend(list(filter(lambda c: not headed(c),
                                       baklinks[nodeid].keys())))
    # if connections:
    #     for connector in connections:


    connections = linkdict[nodeid]
    if connections:
        links = {}
        for connector, link in linkdict[nodeid].items():
            links[connector] = list(_find_paths(
                xmrs, link.end, method, linkdict, seen, maxdepth=maxdepth - 1
            ))
        # beware of magic below:
        #   links maps a connector (like ARG1/NEQ) to a list of subpaths.
        #   This gets the product of subpaths for all connectors, then remaps
        #   the connector to the appropriate subpaths
        lds = map(
            lambda z: dict(zip(links.keys(), z)),
            product(*links.values())
        )
        for ld in lds:
            yield XmrsPathNode(
                nodeid,
                xmrs._graph.node[nodeid]['pred'],
                links=ld,
                depth=depth
            )


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
        path = _read_node(toks, 0, 0)
    except IndexError:
        raise XmrsPathError('Unexpected termination for path: {}'
            .format(path_string))
    if path is None:
        raise XmrsPathError('Error reading path: {}'
            .format(path_string))
    elif toks:
        raise XmrsPathError('Unconsumed tokens: {}'
            .format(', '.join(tok[1] for tok in toks)))
    return path

def _read_node(tokens, depth, distance):
    if not tokens: return None
    mtype, mtext = tokens.popleft()
    if mtype in ('dq_string', 'sq_string', 'symbol'):
        links = _read_links(tokens, depth, distance)
        return XmrsPathNode(
            None,
            Pred.stringpred(mtext),
            links,
            depth,
            distance
        )
    else:
        tokens.appendleft((mtype, mtext))  # put it back
    return None  # current position isn't a path node

def _read_links(tokens, depth, distance):
    if not tokens: return None
    mtype, mtext = tokens.popleft()
    if mtype in ('fwd_connector', 'bak_connector', 'und_connector'):
        connector, subpath = _read_link(
            mtype, mtext, tokens, depth, distance
        )
        return {connector: subpath}
    elif mtext == '(':
        links = {}
        mtype, mtext = tokens.popleft()
        while mtext != ')':
            connector, subpath = _read_link(
                mtype, mtext, tokens, depth, distance
            )
            links[connector] = subpath
            mtype, mtext = tokens.popleft()
            if mtext in ('&', '|'):
                mtype, mtext = tokens.popleft()
            elif mtext != ')':
                raise XmrsPathError('Unexpected token: {}'.format(mtext))
        return links
    else:
        tokens.appendleft((mtype, mtext))  # put it back
    return None  # not a link

def _read_link(mtype, mtext, tokens, depth, distance):
    if mtype == 'fwd_connector':
        return mtext, _read_node(tokens, depth+1, distance+1)
    elif mtype == 'bak_connector':
        return mtext, _read_node(tokens, depth-1, distance+1)
    elif mtype == 'und_connector':
        return mtext, _read_node(tokens, depth, distance+1)
    else:
        raise XmrsPathError('Unexpected token: {}'.format(mtext))