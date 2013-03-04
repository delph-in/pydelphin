
# SimpleMRS codec
# Summary: This module implements serialization and deserialization of
#          the SimpleMRS encoding of Minimal Recusion Semantics. It
#          provides the standard Pickle API calls of load, loads, dump,
#          and dumps.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
import re
from . import mrs
from .mrserrors import MrsDecodeError

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
# the characteristic variable is assumed to be ARG0
_cv             = r'ARG0'
# constant arguments
_constarg      = r'CARG'
def is_carg(x)  : return x == _constarg # for convenience
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
    raise MrsDecodeError('Invalid token: "{}"\tExpected: "{}"'.format(token,
                                                                    expected))

def decode(string):
    return decode_mrs(tokenize(string))

def decode_mrs(tokens):
    """Decode a sequence of Simple-MRS tokens. Assume LTOP, INDEX, RELS,
       and HCONS occur in that order."""
    # [ LTOP : handle INDEX : variable RELS : rels-list HCONS : hcons-list ]
    try:
        validate_token(tokens.pop(0), _left_bracket)
        _, ltop  = read_argument(tokens, rargname=_ltop, sort='h')
        _, index = read_argument(tokens, rargname=_index)
        rels  = read_rels(tokens)
        hcons = read_hcons(tokens)
        validate_token(tokens.pop(0), _right_bracket)
        m = mrs.Mrs(ltop, index, rels, hcons)
    except IndexError:
        unexpected_termination_error()
    return m

def read_argument(tokens, rargname=None, sort=None):
    # RARGNAME : var-or-handle
    name = tokens.pop(0)
    if rargname is not None:
        validate_token(name, rargname)
    validate_token(tokens.pop(0), _colon)
    return name, read_variable(tokens, sort=sort)

def read_variable(tokens, sort=None):
    """Read and return the MrsVariable object for the value of the
       variable. Fail if the sort does not match the expected."""
    # var [ vartype PROP : val ... ]
    var = tokens.pop(0)
    srt, vid = mrs.sort_vid_split(var)
    # consider something like not(srt <= sort) in the case of subsumptive sorts
    if sort is not None and srt != sort:
        raise MrsDecodeError('Variable {} has sort "{}", expected "{}"'.format(
                             var, srt, sort))
    vartype, props = read_props(tokens)
    if vartype is not None and sort != vartype:
        pass #TODO log this as an error?
    if sort == 'h' and props:
        pass #TODO log this as an error?
    return mrs.MrsVariable(sort=srt, vid=vid, properties=props)

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

def read_const(tokens):
    """Read and return a constant argument."""
    # CARG: constant
    carg = tokens.pop(0)
    validate_token(carg, _constarg)
    validate_token(tokens.pop(0), _colon)
    return carg, tokens.pop(0)

def read_rels(tokens):
    """Read and return a RELS set of ElementaryPredications."""
    # RELS: < ep* >
    rels = []
    validate_tokens(tokens, [_rels, _colon, _left_angle])
    # SimpleMRS does not encode a nodeid, and the label cannot be used because
    # it may be shared (e.g. adjectives and the noun they modify), as can ARG0
    # (quantifiers and the quantifiees), so make one up
    nodeid = 10001
    while tokens[0] != _right_angle:
        rels += [read_ep(tokens, nodeid)]
        nodeid += 1
    tokens.pop(0) # we know this is a right angle
    return rels

def read_ep(tokens, nodeid):
    """Read and return an ElementaryPredication."""
    # [ pred LBL : lbl ARG : variable-or-handle ... ]
    # or [ pred < span-from : span-to > ...
    validate_token(tokens.pop(0), _left_bracket)
    pred     = mrs.Pred(tokens.pop(0))
    lnk      = read_lnk(tokens)
    _, label = read_argument(tokens, rargname=_lbl, sort='h')
    cv       = None
    args     = OrderedDict()
    carg     = None
    while tokens[0] != _right_bracket:
        if is_carg(tokens[0]):
            carg = read_constant(tokens)[1]
        elif tokens[0] == _cv:
            _, cv = read_argument(tokens)
        else:
            args.update([read_argument(tokens)])
    tokens.pop(0) # we know this is a right bracket
    return mrs.ElementaryPredication(pred, nodeid, label, cv,
                                     args=args, lnk=lnk, carg=carg)

def read_lnk(tokens):
    """Read and return a tuple of the pred's lnk type and lnk value,
       if a pred lnk is specified."""
    # < FROM : TO > or < FROM # TO > or < TOK... > or < @ EDGE >
    lnktype = None
    lnk = None
    if tokens[0] == _left_angle:
        tokens.pop(0) # we just checked this is a left angle
        if tokens[0] == _right_angle:
            pass # empty <> brackets the same as no lnk specified
        # edge lnk: ['@', EDGE, ...]
        elif tokens[0] == _at:
            tokens.pop(0) # remove the @
            lnktype = mrs.Lnk.EDGE
            lnk = int(tokens.pop(0)) # edge lnks only have one number
        # character span lnk: [FROM, ':', TO, ...]
        elif tokens[1] == _colon:
            lnktype = mrs.Lnk.CHARSPAN
            lnk = (int(tokens.pop(0)), int(tokens.pop(1)))
            tokens.pop(0) # this should be the colon
        # chart vertex range lnk: [FROM, '#', TO, ...]
        elif tokens[1] == _hash:
            lnktype = mrs.Lnk.CHARTSPAN
            lnk = (int(tokens.pop(0)), int(tokens.pop(1)))
            tokens.pop(0) # this should be the hash
        # tokens lnk: [(TOK,)+ ...]
        else:
            lnktype = mrs.Lnk.TOKENS
            lnk = []
            while tokens[0] != _right_angle:
                lnk.append(int(tokens.pop(0)))
        validate_token(tokens.pop(0), _right_angle)
    return mrs.Lnk(lnk, lnktype)

def read_hcons(tokens):
    # HCONS:< HANDLE (qeq|lheq|outscopes) HANDLE ... >
    """Read and return an HCONS list."""
    hcons = []
    validate_tokens(tokens, [_hcons, _colon, _left_angle])
    while tokens[0] != _right_angle:
        lh = read_variable(tokens, sort='h')
        # rels are case-insensitive and the convention is lower-case
        rel = tokens.pop(0).lower()
        if rel == _qeq:
            rel = mrs.HandleConstraint.QEQ
        elif rel == _lheq:
            rel = mrs.HandleConstraint.LHEQ
        elif rel == _outscopes:
            rel = mrs.HandleConstraint.OUTSCOPES
        else:
            invalid_token_error(rel, '('+'|'.join(_valid_hcons)+')')
        rh = read_variable(tokens, sort='h')
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

def encode(m, pretty_print=False):
    """Encode an MRS structure into a SimpleMRS string."""
    # note that listed_vars is modified as a side-effect of the lower
    # functions
    listed_vars = set()
    toks = [' '.join([_left_bracket,
            encode_argument(_ltop, m.ltop, listed_vars),
            encode_argument(_index, m.index, listed_vars)])]
    toks += [encode_rels(m.rels, listed_vars, pretty_print=pretty_print)]
    toks += ['  ' + ' '.join([encode_hcons(m.hcons), _right_bracket])]
    delim = ' ' if not pretty_print else '\n'
    return delim.join(toks)

def encode_argument(rargname, variable, listed_vars):
    """Encode an MRS argument into the SimpleMRS format."""
    return ' '.join([rargname + _colon,
                     encode_variable(variable, listed_vars)])

def encode_variable(var, listed_vars):
    """Encode an MRS variable, and any variable properties, into the
       SimpleMRS format."""
    toks = [str(var)]
    # only encode the variable properties if they haven't been already
    if var.vid not in listed_vars and var.properties:
        toks += [_left_bracket, var.sort]
        for propkey, propval in var.properties.items():
            toks += [propkey + _colon, propval]
        toks += [_right_bracket]
    listed_vars.add(var.vid)
    return ' '.join(toks)

def encode_const(name, const):
    """Encode a constant argument into the SimpleMRS format."""
    # consider checking if const is surrounded by quotes
    return ' '.join([name + _colon, const])

def encode_rels(rels, listed_vars, pretty_print=False):
    """Encode a RELS list of EPs into the SimpleMRS encoding."""
    delim = ' ' if not pretty_print else '\n          '
    string = '  ' + ' '.join([_rels + _colon, _left_angle])
    string += ' ' + delim.join(encode_ep(ep, listed_vars) for ep in rels)
    string += ' ' + _right_angle
    return string

def encode_ep(ep, listed_vars):
    """Encode an Elementary Predication into the SimpleMRS encoding."""
    toks = [_left_bracket]
    toks += [ep.pred.string + encode_lnk(ep.lnk)]
    toks += [encode_argument(_lbl, ep.label, listed_vars)]
    toks += [encode_argument(_cv, ep.cv, listed_vars)]
    for argname, var in ep.args.items():
        toks += [encode_argument(argname, var, listed_vars)]
    # add the constant if it exists
    if ep.carg is not None:
        toks += [encode_const(_constarg, ep.carg)]
    toks += [_right_bracket]
    return ' '.join(toks)

def encode_lnk(lnk):
    """Encode a predication lnk to surface form into the SimpleMRS
       encoding."""
    s = ""
    if lnk is not None:
        s = _left_angle
        if lnk.type == mrs.Lnk.CHARSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), _colon, str(cto)])
        elif lnk.type == mrs.Lnk.CHARTSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), _hash, str(cto)])
        elif lnk.type == mrs.Lnk.TOKENS:
            s += ' '.join([str(t) for t in lnk.data])
        elif lnk.type == mrs.Lnk.EDGE:
            s += ''.join([_at, str(lnk.data)])
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
        toks += [str(hcon.lhandle), rel, str(hcon.rhandle)]
    toks += [_right_angle]
    return ' '.join(toks)
