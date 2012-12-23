
# SimpleMRS codec
# Summary: This module implements serialization and deserialization of
#          the SimpleMRS encoding of Minimal Recusion Semantics. It
#          provides the standard Pickle API calls of load, loads, dump,
#          and dumps.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

import re
from . import mrs
from .mrserrors import MrsDecodeError

_left_bracket = r'['
_right_bracket = r']'
_left_angle = r'<'
_right_angle = r'>'
_colon = r':'
_hash = r'#'
_at = r'@'
_ltop = r'LTOP'
_index = r'INDEX'
_rels = r'RELS'
_hcons = r'HCONS'
_lbl   = r'LBL'
# list of scopal arguments. ARGS matching items here will be parsed as
# handles and not as variables. Also the order these are placed determines
# the order they appear in an encoded SimpleMRS
_scargs = [r'RSTR', r'BODY']
# possible relations for handle constraints
_qeq = r'qeq'
_lheq = r'lheq'
_outscopes = r'outscopes'
_valid_hcons_rels = [_qeq, _lheq, _outscopes]
# possible relations for individual constraints
#_valid_icons_rels = [r'focus', r'topic']

##############################################################################
##############################################################################
### Pickle-API methods

def load(fh):
    if isinstance(fh, str):
        return loads(open(fh,'r').read())
    return loads(fh.read())

def loads(s):
    return decode(s)

def dump(fh, m):
    fh.write(dumps(m))

def dumps(m):
    return encode(m)

##############################################################################
##############################################################################
### Decoding

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

def invalid_token_error(token, expected):
    raise MrsDecodeError('Invalid token: ' + token +\
                         '\n  Expected: ' + expected)

def decode(string):
    return decode_mrs(tokenize(string))

def decode_mrs(tokens):
    """Decode a sequence of Simple-MRS tokens. Assume LTOP, INDEX, RELS,
       and HCONS occur in that order."""
    # [ LTOP : handle INDEX : variable RELS : rels-list HCONS : hcons-list ]
    try:
        validate_token(tokens.pop(0), _left_bracket)
        ltop = read_handle(tokens, _ltop)
        _, index = read_variable(tokens, variable_name=_index)
        rels = read_rels(tokens)
        hcons = read_hcons(tokens)
        validate_token(tokens.pop(0), _right_bracket)
        m = mrs.Mrs(ltop, index, rels, hcons)
    except IndexError:
        unexpected_termination_error()
    return m

def read_handle(tokens, handle_name):
    """Read and return the value of a handle. Handles, such as LTOP and LBL,
       cannot have variable properties following them."""
    # HANDLE : handle
    validate_tokens(tokens, [handle_name, _colon])
    return tokens.pop(0)

def read_variable(tokens, variable_name=None):
    """Read and return the name and MrsVariable object for the value of the
       variable. Fail if variable_name is given and does not match."""
    # VAR : var [ vartype PROP : val ... ]
    name = tokens.pop(0)
    if variable_name:
        validate_token(name, variable_name)
    validate_token(tokens.pop(0), _colon)
    var = tokens.pop(0)
    vartype, props = read_props(tokens)
    return name, mrs.MrsVariable(name=var, sort=vartype, props=props)

def read_props(tokens):
    """Read and return a dictionary of variable properties."""
    # [ vartype PROP1 : val1 PROP2 : val2 ... ]
    props = {}
    if tokens[0] != _left_bracket:  # there might not be any properties
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

def read_rels(tokens):
    """Read and return a RELS set of ElementaryPredications."""
    # RELS: < ep* >
    rels = []
    validate_tokens(tokens, [_rels, _colon, _left_angle])
    while tokens[0] != _right_angle:
        rels += [read_ep(tokens)]
    tokens.pop(0) # we know this is a right angle
    return rels

def read_ep(tokens):
    """Read and return an ElementaryPredication."""
    # [ pred LBL : lbl ARG : variable-or-handle ... ]
    # or [ pred < span-from : span-to > ...
    validate_token(tokens.pop(0), _left_bracket)
    pred = mrs.Pred(tokens.pop(0))
    lnk = read_lnk(tokens)
    label = read_handle(tokens, _lbl)
    ep = mrs.ElementaryPredication(pred=pred, label=label, link=lnk)
    while tokens[0] != _right_bracket:
        if tokens[0] in _scargs:
            scarg = tokens.pop(0)
            validate_token(tokens.pop(0), _colon)
            ep.scargs[scarg] = tokens.pop(0)
        else:
            varname, var = read_variable(tokens)
            ep.args[varname] = var
    tokens.pop(0) # we know this is a right bracket
    return ep

def read_lnk(tokens):
    """Read and return a tuple of the pred's link type and link value,
       if a pred link is specified."""
    # < FROM : TO > or < FROM # TO > or < TOK... > or < @ EDGE >
    lnktype = None
    lnk = None
    if tokens[0] == _left_angle:
        tokens.pop(0) # we just checked this is a left angle
        if tokens[0] == _right_angle:
            pass # empty <> brackets the same as no link specified
        # edge link: ['@', EDGE, ...]
        elif tokens[0] == _at:
            tokens.pop(0) # remove the @
            lnktype = mrs.Link.EDGE
            lnk = int(tokens.pop(0)) # edge links only have one number
        # character span link: [FROM, ':', TO, ...]
        elif tokens[1] == _colon:
            lnktype = mrs.Link.CHARSPAN
            lnk = (int(tokens.pop(0)), int(tokens.pop(1)))
            tokens.pop(0) # this should be the colon
        # chart vertex range link: [FROM, '#', TO, ...]
        elif tokens[1] == _hash:
            lnktype = mrs.Link.CHARTSPAN
            lnk = (int(tokens.pop(0)), int(tokens.pop(1)))
            tokens.pop(0) # this should be the hash
        # tokens link: [(TOK,)+ ...]
        else:
            lnktype = mrs.Link.TOKENS
            lnk = []
            while tokens[0] != _right_angle:
                lnk.append(int(tokens.pop(0)))
        validate_token(tokens.pop(0), _right_angle)
    return mrs.Link(lnk, lnktype)

def read_hcons(tokens):
    # HCONS:< HANDLE (qeq|lheq|outscopes) HANDLE ... >
    """Read and return an HCONS list."""
    hcons = []
    validate_tokens(tokens, [_hcons, _colon, _left_angle])
    while tokens[0] != _right_angle:
        lh = tokens.pop(0)
        # rels are case-insensitive and the convention is lower-case
        rel = tokens.pop(0).lower()
        if rel == _qeq:
            rel = mrs.HandleConstraint.QEQ
        elif rel == _lheq:
            rel = mrs.HandleConstraint.LHEQ
        elif rel == _outscopes:
            rel = mrs.HandleConstraint.OUTSCOPES
        else:
            invalid_token_error(rel, '('+'|'.join(_valid_hcons_rels)+')')
        rh = tokens.pop(0)
        hcons += [mrs.HandleConstraint(lh, rel, rh)]
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

def encode(m):
    """Encode an MRS structure into a SimpleMRS string."""
    # note that listed_vars is modified as a side-effect of the lower
    # functions
    listed_vars = set()
    toks = [_left_bracket]
    toks += [encode_handle(_ltop, m.ltop)]
    toks += [encode_variable(_index, m.index, listed_vars)]
    toks += [encode_rels(m.rels, listed_vars)]
    toks += [encode_hcons(m.hcons)]
    toks += [_right_bracket]
    return ' '.join(toks)

def encode_handle(name, handle):
    """Encode an MRS handle into the SimpleMRS format."""
    return ' '.join([name + _colon, handle])

def encode_variable(name, var, listed_vars):
    """Encode an MRS variable, and any variable properties, into the
       SimpleMRS format."""
    toks = [name + _colon, var.name]
    # only encode the variable properties if they haven't been already
    if var.name not in listed_vars and var.props:
        toks += [_left_bracket, var.sort]
        for propkey, propval in var.props.items():
            toks += [propkey + _colon, propval]
        toks += [_right_bracket]
    listed_vars.add(var.name)
    return ' '.join(toks)

def encode_rels(rels, listed_vars):
    """Encode a RELS list of EPs into the SimpleMRS encoding."""
    toks = [_rels + _colon, _left_angle]
    for ep in rels:
        toks += [encode_ep(ep, listed_vars)]
    toks += [_right_angle]
    return ' '.join(toks)

def encode_ep(ep, listed_vars):
    """Encode an Elementary Predication into the SimpleMRS encoding."""
    toks = [_left_bracket]
    toks += [ep.pred.string + encode_lnk(ep.link)]
    toks += [encode_handle(_lbl, ep.label)]
    # the values of Scalar Args can only be handles
    for scarg, handle in ep.scargs.items():
        toks += [scarg + _colon, handle]
    # the values of regular args are variables
    for arg, var in ep.args.items():
        toks += [encode_variable(arg, var, listed_vars)]
    toks += [_right_bracket]
    return ' '.join(toks)

def encode_lnk(link):
    """Encode a predication link to surface form into the SimpleMRS
       encoding."""
    s = ""
    if link is not None:
        s = _left_angle
        if link.type == mrs.Link.CHARSPAN:
            cfrom, cto = link.data
            s += ''.join([str(cfrom), _colon, str(cto)])
        elif link.type == mrs.Link.CHARTSPAN:
            cfrom, cto = link.data
            s += ''.join([str(cfrom), _hash, str(cto)])
        elif link.type == mrs.Link.TOKENS:
            s += ' '.join([str(t) for t in link.data])
        elif link.type == mrs.Link.EDGE:
            s += ''.join([_at, str(link.data)])
        s += _right_angle
    return s

def encode_hcons(hcons):
    """Encode a Handle Constraint into the SimpleMRS encoding."""
    toks = [_hcons + _colon, _left_angle]
    for hcon in hcons:
        if hcon.relation == mrs.HandleConstraint.QEQ:
            rel = _qeq
        elif hcon.relation == mrs.HandleConstraint.LHEQ:
            rel = _lheq
        elif hcon.relation == mrs.HandleConstraint.OUTSCOPES:
            rel = _outscopes
        toks += [hcon.lhandle, rel, hcon.rhandle]
    toks += [_right_angle]
    return ' '.join(toks)
