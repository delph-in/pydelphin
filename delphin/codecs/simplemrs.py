
# SimpleMRS codec
# Summary: This module implements serialization and deserialization of
#          the SimpleMRS encoding of Minimal Recusion Semantics. It
#          provides the standard Pickle API calls of load, loads, dump,
#          and dumps.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
import re
from delphin.mrs import (Mrs, ElementaryPredication, Argument, Pred,
                         MrsVariable, Lnk, HandleConstraint)
from delphin.mrs.var import (sort_vid_split, sort_vid_re)
from delphin.mrs.config import (HANDLESORT, CVARG, CONSTARG,
                                QEQ, LHEQ, OUTSCOPES,
                                CHARSPAN, CHARTSPAN, EDGE, TOKENS,
                                VARIABLE_ARG, HOLE_ARG, CONSTANT_ARG)
from delphin._exceptions import MrsDecodeError

strict = False

_left_bracket   = r'['
_right_bracket  = r']'
_left_angle     = r'<'
_right_angle    = r'>'
_colon          = r':'
_hash           = r'#'
_at             = r'@'
_ltop           = r'LTOP'
_index          = r'INDEX'
_rels           = r'RELS'
_hcons          = r'HCONS'
_lbl            = r'LBL'
# possible relations for handle constraints
_qeq            = r'qeq'
_lheq           = r'lheq'
_outscopes      = r'outscopes'
_valid_hcons    = [_qeq, _lheq, _outscopes]
# possible relations for individual constraints
#_valid_icons    = [r'focus', r'topic']

##############################################################################
##############################################################################
### Pickle-API methods

def load(fh):
    """
    Deserialize a SimpleMRS from a file (handle or filename)

    Args:
        fh: filename or file object
    Returns:
        an Xmrs object
    """
    if isinstance(fh, str):
        return loads(open(fh,'r').read())
    return loads(fh.read())

def loads(s):
    """
    Deserialize an MRS from a SimpleMRS string representation

    Args:
        s: a SimpleMRS string
    Returns:
        an Xmrs object
    """
    return deserialize(s)

def dump(fh, m, pretty_print=False):
    """
    Serialize an Xmrs object to a SimpleMRS representation and write to a file

    Args:
        fh: filename or file object
        m: the Xmrs object to Serialize
        encoding: the character encoding for the file
        pretty_print: if true, the output is formatted to be easier to read
    """
    print(dumps(m, pretty_print=pretty_print), file=fh)

def dumps(m, pretty_print=False):
    """
    Serialize an Xmrs object to a SimpleMRS representation

    Args:
        m: the Xmrs object to Serialize
        pretty_print: if true, the output is formatted to be easier to read
    Returns:
        a SimpleMrs string
    """
    return serialize(m, pretty_print=pretty_print)

##############################################################################
##############################################################################
### Deserialization

# The tokenizer has 3 sub-regexen:
#   the first is for strings (e.g. "_dog_n_rel", "\"quoted string\"")
#   the second is for args, variables, preds, etc (e.g. ARG1, _dog_n_rel, x4)
#   the last is for contentful punctuation (e.g. [ ] < > : # @)
tokenizer = re.compile(r'("[^"\\]*(?:\\.[^"\\]*)*"' +\
                       r'|[^\s:#@\[\]<>"]+' +\
                       r'|[:#@\[\]<>])')
def tokenize(string):
    """Split the SimpleMrs string into tokens."""
    return tokenizer.findall(string)

def validate_token(token, expected):
    """Make sure the given token is as expected, or raise an error. This
       comparison is case insensitive."""
    # uppercase the input, since expected tokens are all upper case
    if token.upper() != expected:
        invalid_token_error(token, expected)

def validate_tokens(tokens, expected):
    for exp_tok in expected:
        validate_token(tokens.pop(0), exp_tok)

def is_variable(token):
    return sort_vid_re.match(token) is not None

def invalid_token_error(token, expected):
    raise MrsDecodeError('Invalid token: "{}"\tExpected: "{}"'
                         .format(token, expected))

def deserialize(string):
    return read_mrs(tokenize(string))

def read_mrs(tokens):
    """Decode a sequence of Simple-MRS tokens. Assume LTOP, INDEX, RELS,
       and HCONS occur in that order."""
    # variables needs to be passed to any function that can call read_variable
    variables = {}
    # [ LTOP : handle INDEX : variable RELS : rels-list HCONS : hcons-list ]
    try:
        validate_token(tokens.pop(0), _left_bracket)
        if tokens[0] == _ltop:
            _, ltop  = read_featval(tokens, feat=_ltop, variables=variables)
        if tokens[0] == _index:
            _, index = read_featval(tokens, feat=_index, variables=variables)
        rels  = read_rels(tokens, variables=variables)
        hcons = read_hcons(tokens, variables=variables)
        validate_token(tokens.pop(0), _right_bracket)
        m = Mrs(ltop, index, rels, hcons)
    except IndexError:
        unexpected_termination_error()
    return m

def read_featval(tokens, feat=None, sort=None, variables=None):
    # FEAT : (var-or-handle|const)
    if variables is None: variables = {}
    name = tokens.pop(0)
    if feat is not None:
        validate_token(name, feat)
    validate_token(tokens.pop(0), _colon)
    # if it's not a variable, assume it's a constant
    if is_variable(tokens[0]):
        value = read_variable(tokens, sort=sort, variables=variables)
    else:
        value = tokens.pop(0)
    return name, value

def read_variable(tokens, sort=None, variables=None):
    """Read and return the MrsVariable object for the value of the
       variable. Fail if the sort does not match the expected."""
    # var [ vartype PROP : val ... ]
    if variables is None: variables = {}
    var = tokens.pop(0)
    srt, vid = sort_vid_split(var)
    # consider something like not(srt <= sort) in the case of subsumptive sorts
    if sort is not None and srt != sort:
        raise MrsDecodeError('Variable {} has sort "{}", expected "{}"'.format(
                             var, srt, sort))
    vartype, props = read_props(tokens)
    if vartype is not None and srt != vartype:
        raise MrsDecodeError('Variable "{}" and its cvarsort "{}" are '
                             'not the same.'.format(var, vartype))
    if srt == 'h' and props:
        raise MrsDecodeError('Handle variable "{}" has a non-empty '
                             'property set {}.'.format(var, props))
    if vid in variables:    
        if srt != variables[vid].sort:
            raise MrsDecodeError('Variable {} has a conflicting sort with {}'
                                 .format(var, str(variables[vid])))
        variables[vid].properties.update(props)
    else:
        variables[vid] = MrsVariable(vid=vid, sort=srt, properties=props)
    return variables[vid]

def read_props(tokens):
    """Read and return a dictionary of variable properties."""
    # [ vartype PROP1 : val1 PROP2 : val2 ... ]
    props = OrderedDict()
    if not tokens or tokens[0] != _left_bracket:
        return None, props
    tokens.pop(0) # get rid of bracket (we just checked it)
    vartype = tokens.pop(0)
    # check if a vartype wasn't given (next token is : )
    if tokens[0] == _colon:
        invalid_token_error(vartype, "variable type")
    while tokens[0] != _right_bracket:
        prop = tokens.pop(0)
        validate_token(tokens.pop(0), _colon)
        val = tokens.pop(0)
        props[prop] = val
    tokens.pop(0) # we know this is a right bracket
    return vartype, props

def read_rels(tokens, variables=None):
    """Read and return a RELS set of ElementaryPredications."""
    # RELS: < ep* >
    if variables is None: variables = {}
    rels = []
    validate_tokens(tokens, [_rels, _colon, _left_angle])
    while tokens[0] != _right_angle:
        rels += [read_ep(tokens, variables=variables)]
    tokens.pop(0) # we know this is a right angle
    return rels

def read_ep(tokens, variables=None):
    """Read and return an ElementaryPredication."""
    # [ pred LBL : lbl ARG : variable-or-handle ... ]
    # or [ pred < lnk > ...
    if variables is None: variables = {}
    validate_token(tokens.pop(0), _left_bracket)
    pred     = Pred.string_or_grammar_pred(tokens.pop(0))
    lnk      = read_lnk(tokens)
    _, label = read_featval(tokens, feat=_lbl, sort=HANDLESORT,
                            variables=variables)
    args     = []
    while tokens[0] != _right_bracket:
        args.append(read_argument(tokens, variables=variables))
    tokens.pop(0) # we know this is a right bracket
    return ElementaryPredication(pred, label, args=args, lnk=lnk)

def read_argument(tokens, variables=None):
    """Read and return an Argument."""
    # ARGNAME: (VAR|CONST)
    if variables is None: variables = {}
    argname, value = read_featval(tokens, variables=variables)
    #argtype = CONSTANTARG # default in case others don't match
    #if isinstance(value, MrsVariable):
    #    if value.sort == HANDLESORT:
    #        argtype = HOLE_ARG
    #    else:
    #        argtype = VARIABLEARG
    return Argument.mrs_argument(argname, value)

def read_lnk(tokens):
    """Read and return a tuple of the pred's lnk type and lnk value,
       if a pred lnk is specified."""
    # < FROM : TO > or < FROM # TO > or < TOK... > or < @ EDGE >
    lnktype = None
    lnk = None
    if tokens and tokens[0] == _left_angle:
        tokens.pop(0) # we just checked this is a left angle
        if tokens[0] == _right_angle:
            pass # empty <> brackets the same as no lnk specified
        # edge lnk: ['@', EDGE, ...]
        elif tokens[0] == _at:
            tokens.pop(0) # remove the @
            lnk = Lnk.edge(tokens.pop(0)) # edge lnks only have one number
        # character span lnk: [FROM, ':', TO, ...]
        elif tokens[1] == _colon:
            lnk = Lnk.charspan(tokens.pop(0), tokens.pop(1))
            tokens.pop(0) # this should be the colon
        # chart vertex range lnk: [FROM, '#', TO, ...]
        elif tokens[1] == _hash:
            lnk = Lnk.chartspan(tokens.pop(0), tokens.pop(1))
            tokens.pop(0) # this should be the hash
        # tokens lnk: [(TOK,)+ ...]
        else:
            lnkdata = []
            while tokens[0] != _right_angle:
                lnkdata.append(int(tokens.pop(0)))
            lnk = Lnk.tokens(lnkdata)
        validate_token(tokens.pop(0), _right_angle)
    return lnk

def read_hcons(tokens, variables=None):
    # HCONS:< HANDLE (qeq|lheq|outscopes) HANDLE ... >
    """Read and return an HCONS list."""
    if variables is None: variables = {}
    hcons = []
    validate_tokens(tokens, [_hcons, _colon, _left_angle])
    while tokens[0] != _right_angle:
        hi = read_variable(tokens, sort='h', variables=variables)
        # rels are case-insensitive and the convention is lower-case
        rel = tokens.pop(0).lower()
        if rel == _qeq:
            rel = QEQ
        elif rel == _lheq:
            rel = LHEQ
        elif rel == _outscopes:
            rel = OUTSCOPES
        else:
            invalid_token_error(rel, '('+'|'.join(_valid_hcons)+')')
        lo = read_variable(tokens, sort='h', variables=variables)
        hcons += [HandleConstraint(hi, rel, lo)]
    tokens.pop(0) # we know this is a right angle
    return hcons

#def read_icons(tokens):
#    # ICONS:<>
#    pass

def unexpected_termination_error():
    raise MrsDecodeError('Invalid MRS: Unexpected termination.')

##############################################################################
##############################################################################
### Encoding

def serialize(m, pretty_print=False):
    """Serialize an MRS structure into a SimpleMRS string."""
    # note that listed_vars is modified as a side-effect of the lower
    # functions
    listed_vars = set()
    toks = [_left_bracket]
    if m.ltop is not None:
        toks += [serialize_argument(_ltop, m.ltop, listed_vars)]
    if m.index is not None:
        toks += [serialize_argument(_index, m.index, listed_vars)]
    toks = [' '.join(toks)]
    toks += [serialize_rels(m.rels, listed_vars, pretty_print=pretty_print)]
    toks += ['  ' + ' '.join([serialize_hcons(m.hcons), _right_bracket])]
    delim = ' ' if not pretty_print else '\n'
    return delim.join(toks)

def serialize_argument(rargname, variable, listed_vars):
    """Serialize an MRS argument into the SimpleMRS format."""
    return ' '.join([rargname + _colon,
                     serialize_variable(variable, listed_vars)])

def serialize_variable(var, listed_vars):
    """Serialize an MRS variable, and any variable properties, into the
       SimpleMRS format."""
    toks = [str(var)]
    # only serialize the variable properties if they haven't been already
    if var.vid not in listed_vars and var.properties:
        toks += [_left_bracket, var.sort]
        for propkey, propval in var.properties.items():
            toks += [propkey.upper() + _colon, propval]
        toks += [_right_bracket]
    listed_vars.add(var.vid)
    return ' '.join(toks)

def serialize_const(name, const):
    """Serialize a constant argument into the SimpleMRS format."""
    # consider checking if const is surrounded by quotes
    return ' '.join([name + _colon, const])

def serialize_rels(rels, listed_vars, pretty_print=False):
    """Serialize a RELS list of EPs into the SimpleMRS encoding."""
    delim = ' ' if not pretty_print else '\n          '
    string = '  ' + ' '.join([_rels + _colon, _left_angle])
    string += ' ' + delim.join(serialize_ep(ep, listed_vars) for ep in rels)
    string += ' ' + _right_angle
    return string

def serialize_ep(ep, listed_vars):
    """Serialize an Elementary Predication into the SimpleMRS encoding."""
    toks = [_left_bracket]
    toks += [ep.pred.string + serialize_lnk(ep.lnk)]
    toks += [serialize_argument(_lbl, ep.label, listed_vars)]
    #if ep.cv is not None:
    #    toks += [serialize_argument(CVARG, ep.cv, listed_vars)]
    for arg in ep.args:
        toks += [serialize_argument(arg.argname, arg.value, listed_vars)]
    # add the constant if it exists (currently done as a regular arg above)
    #if ep.carg is not None:
    #    toks += [serialize_const(CONSTARG, ep.carg)]
    toks += [_right_bracket]
    return ' '.join(toks)

def serialize_lnk(lnk):
    """Serialize a predication lnk to surface form into the SimpleMRS
       encoding."""
    s = ""
    if lnk is not None:
        s = _left_angle
        if lnk.type == CHARSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), _colon, str(cto)])
        elif lnk.type == CHARTSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), _hash, str(cto)])
        elif lnk.type == TOKENS:
            s += ' '.join([str(t) for t in lnk.data])
        elif lnk.type == EDGE:
            s += ''.join([_at, str(lnk.data)])
        s += _right_angle
    return s

def serialize_hcons(hcons):
    """Serialize a Handle Constraint into the SimpleMRS encoding."""
    toks = [_hcons + _colon, _left_angle]
    for hcon in hcons:
        if hcon.relation == QEQ:
            rel = _qeq
        elif hcon.relation == LHEQ:
            rel = _lheq
        elif hcon.relation == OUTSCOPES:
            rel = _outscopes
        toks += [str(hcon.hi), rel, str(hcon.lo)]
    toks += [_right_angle]
    return ' '.join(toks)
