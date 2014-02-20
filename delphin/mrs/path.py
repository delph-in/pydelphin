import re
from collections import deque
from .pred import is_valid_pred_string

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

_path_end_tokens = set([')',']','|','&']) # also empty input; check separately
_top_vars = set(['LTOP', 'INDEX'])
_expression_operators = set(['=', 'is'])
_non_pred_toks = set([':','/','%','^','~','@',')','[',']','=','&','|']) #'('

tokenizer = re.compile(
    r'\s*("[^"\\]*(?:\\.[^"\\]*)*"|' # quoted strings
    r'[^\s*#:/%^~@()\[\]=&|]+|'      # non-breaking characters
    r'[*#:/%^~@()\[\]=&|])\s*'       # meaningful punctuation
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
        steps.popleft() # get rid of '|'
        objs.extend(_traverse_conjunction(xmrs, obj, steps, traverser,
                                          context))
    return objs

def _traverse_conjunction(xmrs, obj, steps, traverser, context=None):
    objs = traverser(xmrs, obj, steps, context)
    # &-ops can fail early, since all must evaluate to True to be
    # used, but we can't short-circuit conjunction unless we know how
    # many steps to remove from the queue, so just parse them for now
    while steps and steps[0] == '&':
        steps.popleft() # get rid of '&'
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
    steps.popleft() # remove '('
    objs = _traverse_disjunction(xmrs, obj, steps, _traverse_pathexpr,
                                 context)
    steps.popleft() # remove ')'

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
            return objs
            elif step == '[':
            if traverse(xmrs, curobj, steps):
                objs.append(curobj)
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
    # / -> ARG/pred -> value of ARG is CV of pred, labels not shared
    # # -> ARG#pred -> value of ARG is CV of pred, label shared
    # # -> pred1#pred2 -> pred1 and pred2 share a label
    # ^ -> ARG^pred -> value of ARG is pred's label
    # ~ -> ARG~pred -> value of ARG is QEQ'd to pred's label
    #_chase_v_1_rel
    #_chase_v_1_rel:ARG1
    #_chase_v_1_rel:ARG1/_dog_n_1_rel
    #_think_v_1_rel:ARG2^_chase_v_1_rel
    #_big_a_1_rel:ARG1#_dog_n_1_rel
    #_the_q_rel:RSTR~_dog_n_1_rel
    #_the_q_rel[RSTR~_dog_n_1_rel]
    #_dog_n_1_rel=_wag_v_1_rel
    # with recursion:
    #  for "the dog barked"
    #_bark_v_1_rel:ARG1/(_the_q_rel:RSTR~_dog_n_1_rel)
    #  but needs 2 _dog_n_1_rels for "the dog whose tail wagged barked"
    #_bark_v_1_rel:ARG1/(
    #   _the_q_rel:RSTR~(
    #       _wag_v_1_rel(ARG1/(
    #           def_explicit_q_rel:RSTR~(
    #               poss_rel:ARG1/_tail_n_1_rel
    #           )
    #       )=_dog_n_1_rel
    #   )
    #)
    # with memory:
    # bark:ARG1/(the:RSTR~#1[dog]) &\
    #    #1:LBL^wag:ARG1/(def:RSTR~#2[tail]) &\
        #    poss:(ARG1/#2 & ARG2=#1)
        #compound_rel(ARG1=_ & ARG2/_)
        #and{(L-HNDL^ & L-INDEX/)bark & (R-HNDL^ & R-INDEX)sleep???
