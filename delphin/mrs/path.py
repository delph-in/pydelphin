import re
from collections import deque, defaultdict
from itertools import product
from .components import Pred
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

tokenizer = re.compile(
    r'\s*("[^"\\]*(?:\\.[^"\\]*)*"|'  # quoted strings
    r'[^\s*#:/%^~@()\[\]=&|]+|'       # non-breaking characters
    r'[*#:/%^~@()\[\]=&|])\s*'        # meaningful punctuation
)


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
        for nid in get_nodeids(path_node):
            yield nid


def get_preds(path):
    yield path.pred
    for link, path_node in path:
        for pred in get_preds(path_node):
            yield pred


def sort_rargs(rargs):
    # put LBL at the start, BODY at the end, otherwise alphabetically sort
    return sorted(rargs, key=lambda x: (x != 'LBL', x == 'BODY', x))


def format_path(path, rargsort=sort_rargs):
    if path is None:
        return ''
    links = [':{}>{}'.format(rarg, format_path(path.links[rarg]))
             for rarg in rargsort(path.links.keys())]
    if len(links) > 1:
        subpath = '({})'.format(' & '.join(links))
    else:
        subpath = ''.join(links)  # possibly just ''
    return '{}{}'.format(path.pred.string, subpath)

def find_paths(xmrs, allow_eq=False):
    linkdict = defaultdict(dict)
    for link in xmrs.links:
        if link.argname or allow_eq:
            connector = '{}/{}'.format(link.argname, link.post)
            linkdict[link.start][connector] = link
            # undirected eq links look directed, so add them both ways
            if link.argname == '':
                linkdict[link.end][connector] = link
    explored = set()
    for nid in xmrs.nodeids:
        if nid in explored:
            continue  # might have already been there because of _find_paths
        for path in _find_paths(xmrs, nid, linkdict):
            explored.add(path.nodeid)
            yield path

def _find_paths(xmrs, nodeid, linkdict):
    g = xmrs._graph
    srcnode = g.node[nodeid]
    pred = srcnode['pred']
    # just the pred
    #yield XmrsPathNode(nodeid, pred)
    # pred and all arguments unfulfilled (e.g. "_bark_v_1_rel:ARG1/NEQ>")
    yield XmrsPathNode(
        nodeid, pred, links=dict((c, None) for c in linkdict.get(nodeid,{}))
    )
    # pred and all fulfilled arguments
    connections = linkdict[nodeid]
    if connections:
        links = {}
        for connector, link in linkdict[nodeid].items():
            links[connector] = list(_find_paths(xmrs, link.end, linkdict))
        # beware of magic below:
        #   links maps a connector (like ARG1/NEQ) to a list of subpaths
        #   this gets the product of subpaths for all connectors, then remaps
        #   the connector to the appropriate subpaths
        lds = map(
            lambda z: dict(zip(links.keys(), z)),
            product(*links.values())
        )
        for ld in lds:
            yield XmrsPathNode(nodeid, pred, links=ld)
