import re
from collections import deque
from itertools import product
from .pred import is_valid_pred_string
from .util import powerset

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
    elif is_valid_pred_string(step, suffix_required=False):
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
    def __init__(self, path, preds):
        self.path = path
        self.preds = tuple(sorted(preds or []))

    def __str__(self):
        return self.path


def get_paths(xmrs, **kwargs):
    for nid in xmrs.nodeids:
        for (eppath, preds) in get_ep_paths(xmrs, nid, **kwargs):
            yield XmrsPath(eppath, preds)


def get_ep_paths(xmrs, nid, path=None, max_depth=-1, allow_bare_args=False):
    # ep[argpaths]
    if max_depth == 0:
        raise StopIteration
    pred = xmrs.get_pred(nid)
    path = '{}{}'.format(path or '', pred.short_form())
    args = xmrs.get_outbound_args(nid, allow_unbound=False)
    for argset in powerset(args):
        numargs = len(argset)
        if numargs == 0:
            yield (path, [pred])
        else:
            arg_path_conj = get_arg_path_conj(
                xmrs, argset, path=path,
                max_depth=max_depth,
                allow_bare_args=allow_bare_args
            )
            for (subpath, subpreds) in arg_path_conj:
                yield (subpath, [pred] + subpreds)


def get_arg_path_conj(xmrs, args, path=None,
                      max_depth=-1,
                      allow_bare_args=False):
    # :argpath or (:argpath [& :argpath]*)
    if allow_bare_args:
        yield join_subpaths(path, [':{}'.format(arg.argname) for arg in args])
    # beware of magic below:
    # first, get_subpaths is a function that gets subpaths for an arg
    get_subpaths = lambda x: list(get_arg_paths(xmrs, x, max_depth=max_depth))
    # then map that function on all args, and get all combinations of
    # the subpaths with itertools.product.
    subpath_sets = product(*list(map(get_subpaths, args)))
    print(list(subpath_sets))
    for subpaths, subpreds in subpath_sets:
        yield (join_subpaths(path, [':{}'.format(sp) for sp in subpaths]),
               subpreds)


def join_subpaths(basepath, subpaths, joiner=' & '):
    if len(subpaths) == 1:
        pathstring = '{}{}'
    elif len(subpaths) > 1:
        pathstring = '{}({})'
    else:
        raise ValueError("There must be more than one subpath.")
    return pathstring.format(basepath or '', joiner.join(subpaths))


def get_arg_paths(xmrs, arg, max_depth=-1):
    op, tgtnid = get_arg_op_and_target(xmrs, arg)
    yield '{}{}'.format(arg.argname, op)
    for eppath in get_ep_paths(xmrs, tgtnid, max_depth=max_depth-1):
        yield '{}{}{}'.format(arg.argname, op, eppath)


def get_arg_op_and_target(xmrs, arg):
    op = tgtnid = None
    get_label = xmrs.get_label
    if arg.value in xmrs._cv_to_nid:
        tgtnid = xmrs._cv_to_nid[arg.value]
        op = '%' if get_label(arg.nodeid) == get_label(tgtnid) else '/'
    elif arg.value in xmrs._label_to_nids:
        tgtnid = xmrs.find_scope_head(arg.value)
        op = '^'
    elif arg.value in xmrs._var_to_hcons:
        tgtnid = xmrs.find_scope_head(arg.value)
        op = '~'
    return op, tgtnid