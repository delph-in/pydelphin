import re
from collections import deque

# Something like this:
#
# MrsPathExpr    = OrPathExpr | ParenPathExpr
# ParenPathExpr  = '(' OrPathExpr ')'
# OrPathExpr     = AndPathExpr | AndPathExpr '|' OrPathExpr
# AndPathExpr    = PathExpr | PathExpr '&' AndPathExpr
# EPPath         = EP EPCondition ArgPath
# EP             = Pred | '#' NodeIdOrAnchor | '*'
# NodeIdOrAnchor = NodeId | Anchor
# EPCondition    = '[' Condition ']' | None
# Condition      = MrsPathExpr Comparison
# Comparision    = '=' MrsPathExpr | '=' String | None
# ArgPath        = ':' ArgName ArgPost | None
# ArgName        = '*' | String
# ArgPost        = PostOperator PostPath | None
# PostOperator   = '/' | '%' | '^' | '~'
# PostPath       = EPPath | ParenPathExpr

tokenizer = re.compile(
    r'\s*("[^"\\]*(?:\\.[^"\\]*)*"|' # quoted strings
    r'[^\s*#:/%^~@()\[\]=&|]+|'      # non-breaking characters
    r'[*#:/%^~@()\[\]=&|])\s*'       # meaningful punctuation
)
non_pred_toks = set([':','/','%','^','~','@',')','[',']','=','&','|']) #'('

def tokenize(path):
    """Split the path into tokens."""
    return tokenizer.findall(path)

def walk(xmrs, path):
    # for now path is space separated
    path_tokens = path.split()

def traverse(xmrs, obj, steps):
    objs = _traverse_path_conjunction(xmrs, obj, steps)
    while steps:
        if steps[0] == '|':
            objs.extend(_traverse_path_conjunction(xmrs, obj, steps))
        else:
            raise Exception('Mrs Path expected "|", got {}'.format(steps[0]))
    return objs

def _traverse_path_conjunction(xmrs, obj, steps):
    objs = _traverse_path(xmrs, obj, steps)
    # &-ops can fail early, since all must evaluate to True to be
    # used, but we can't short-circuit conjunction unless we know how
    # many steps to remove from the queue, so just parse them for now
    while steps:
        if steps[0] == '&':
            objs2 = _traverse_path(xmrs, obj, steps)
            if objs and objs2:
                objs.extend(objs2)
            else:
                objs = []
        else:
            raise Exception('Mrs Path expected "&", got {}'.format(steps[0]))
    return objs

def _traverse_path(xmrs, obj, steps):
    objs = []
    while steps:
        step = steps.popleft()
        if step == '*':
            pass
        elif step == '(':
            objs.extend(traverse(xmrs, curobj, steps))
        elif step.upper() == 'LTOP':
            pass
        elif step.upper() == 'INDEX':
            pass
        elif step == '#':
             traverse(xmrs.get_ep)
        elif step not in non_pred_toks:
            curobj = step
    return objs


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
