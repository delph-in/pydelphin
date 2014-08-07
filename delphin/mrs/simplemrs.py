
# SimpleMRS codec
# Summary: This module implements serialization and deserialization of
#          the SimpleMRS encoding of Minimal Recusion Semantics. It
#          provides the standard Pickle API calls of load, loads, dump,
#          and dumps.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
import re
from delphin.mrs import Mrs
from delphin.mrs.components import (
    Hook, ElementaryPredication, Argument, Pred,
    MrsVariable, Lnk, HandleConstraint, sort_vid_split, sort_vid_re
)
from delphin.mrs.config import (HANDLESORT, QEQ, LHEQ, OUTSCOPES)
from delphin._exceptions import MrsDecodeError

# versions are:
#  * 1.0 long running standard
#  * 1.1 added support for MRS-level lnk, surface and EP-level surface
_default_version = 1.1
_latest_version = 1.1

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
_lbl = r'LBL'
# possible relations for handle constraints
_qeq = r'qeq'
_lheq = r'lheq'
_outscopes = r'outscopes'
_valid_hcons = [_qeq, _lheq, _outscopes]
# possible relations for individual constraints
# _valid_icons    = [r'focus', r'topic']

# pretty-print options
_default_mrs_delim = '\n'

# color options
bold = lambda x: '\x1b[1m{}\x1b[0m'.format(x)
gray = lambda x: '\x1b[90m{}\x1b[39;49m'.format(x)
red = lambda x: '\x1b[31m{}\x1b[39;49m'.format(x)
magenta = lambda x: '\x1b[95m{}\x1b[39;49m'.format(x)
blue = lambda x: '\x1b[94m{}\x1b[39;49m'.format(x)
darkgreen = lambda x: '\x1b[32m{}\x1b[39;49m'.format(x)
green = lambda x: '\x1b[92m{}\x1b[39;49m'.format(x)
yellow = lambda x: '\x1b[33m{}\x1b[39;49m'.format(x)

##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    """
    Deserialize SimpleMRSs from a file (handle or filename)

    Args:
      fh: filename or file object
      single: if True, only return the first read |Xmrs| object
    Returns:
      a generator of Xmrs objects (unless the *single* option is True)
    """
    if isinstance(fh, str):
        return loads(open(fh, 'r').read(), single=single)
    return loads(fh.read(), single=single)


def loads(s, single=False):
    """
    Deserialize SimpleMRS string representations

    Args:
      s: a SimpleMRS string
      single: if True, only return the first read Xmrs object
    Returns:
      a generator of Xmrs objects (unless the *single* option is True)
    """
    ms = deserialize(s)
    if single:
        return next(ms)
    else:
        return ms


def dump(fh, ms, single=False, version=_default_version,
         pretty_print=False, color=False, **kwargs):
    """
    Serialize Xmrs objects to a SimpleMRS representation and write to a
    file

    Args:
      fh: filename or file object
      ms: an iterator of Xmrs objects to serialize (unless the
        *single* option is True)
      single: if True, treat ms as a single Xmrs object instead of
        as an iterator
      pretty_print: if True, the output is formatted to be easier to
        read
      color: if True, colorize the output with ANSI color codes
    Returns:
      None
    """
    print(dumps(ms,
                single=single,
                version=version,
                pretty_print=pretty_print,
                color=color,
                **kwargs),
          file=fh)


def dumps(ms, single=False, version=_default_version,
          pretty_print=False, color=False, **kwargs):
    """
    Serialize an Xmrs object to a SimpleMRS representation

    Args:
      ms: an iterator of Xmrs objects to serialize (unless the
        *single* option is True)
      single: if True, treat ms as a single Xmrs object instead of
        as an iterator
      pretty_print: if True, the output is formatted to be easier to
        read
      color: if True, colorize the output with ANSI color codes
    Returns:
        a SimpleMrs string representation of a corpus of Xmrs
    """
    if single:
        ms = [ms]
    return serialize(ms, version=version,
                     pretty_print=pretty_print, color=color, **kwargs)


# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Deserialization

# The tokenizer has 3 sub-regexen:
#   the first is for strings (e.g. "_dog_n_rel", "\"quoted string\"")
#   the second is for args, variables, preds, etc (e.g. ARG1, _dog_n_rel, x4)
#   the last is for contentful punctuation (e.g. [ ] < > : # @)

tokenizer = re.compile(r'("[^"\\]*(?:\\.[^"\\]*)*"'
                       r'|[^\s:#@\[\]<>"]+'
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
    # FIXME: consider buffering this so we don't read the whole string at once
    tokens = tokenize(string)
    while tokens:
        yield read_mrs(tokens)


def read_mrs(tokens, version=_default_version):
    """Decode a sequence of Simple-MRS tokens. Assume LTOP, INDEX, RELS,
       and HCONS occur in that order."""
    # variables needs to be passed to any function that can call read_variable
    variables = {}
    # [ LTOP : handle INDEX : variable RELS : rels-list HCONS : hcons-list ]
    try:
        validate_token(tokens.pop(0), _left_bracket)
        ltop = index = surface = lnk = None
        # SimpleMRS extension for encoding surface string
        if tokens[0] == _left_angle:
            lnk = read_lnk(tokens)
        if tokens[0].startswith('"'): # and tokens[0].endswith('"'):
            surface = tokens.pop(0)[1:-1] # get rid of first quotes
        if tokens[0] == _ltop:
            _, ltop = read_featval(tokens, feat=_ltop, variables=variables)
        if tokens[0] == _index:
            _, index = read_featval(tokens, feat=_index, variables=variables)
        rels = read_rels(tokens, variables=variables)
        hcons = read_hcons(tokens, variables=variables)
        validate_token(tokens.pop(0), _right_bracket)
        m = Mrs(hook=Hook(ltop=ltop, index=index),
                rels=rels,
                hcons=hcons,
                lnk=lnk,
                surface=surface)
    except IndexError:
        unexpected_termination_error()
    return m


def read_featval(tokens, feat=None, sort=None, variables=None):
    # FEAT : (var-or-handle|const)
    if variables is None:
        variables = {}
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
    if variables is None:
        variables = {}
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
    tokens.pop(0)  # get rid of bracket (we just checked it)
    vartype = tokens.pop(0)
    # check if a vartype wasn't given (next token is : )
    if tokens[0] == _colon:
        invalid_token_error(vartype, "variable type")
    while tokens[0] != _right_bracket:
        prop = tokens.pop(0)
        validate_token(tokens.pop(0), _colon)
        val = tokens.pop(0)
        props[prop] = val
    tokens.pop(0)  # we know this is a right bracket
    return vartype, props


def read_rels(tokens, variables=None):
    """Read and return a RELS set of ElementaryPredications."""
    # RELS: < ep* >
    if variables is None:
        variables = {}
    rels = []
    validate_tokens(tokens, [_rels, _colon, _left_angle])
    while tokens[0] != _right_angle:
        rels += [read_ep(tokens, variables=variables)]
    tokens.pop(0)  # we know this is a right angle
    return rels


def read_ep(tokens, variables=None):
    """Read and return an ElementaryPredication."""
    # [ pred LBL : lbl ARG : variable-or-handle ... ]
    # or [ pred < lnk > ...
    if variables is None:
        variables = {}
    validate_token(tokens.pop(0), _left_bracket)
    pred = Pred.string_or_grammar_pred(tokens.pop(0))
    lnk = read_lnk(tokens)
    if tokens[0].startswith('"'):
        surface = tokens.pop(0)[1:-1] # get rid of first quotes
    else:
        surface = None
    _, label = read_featval(tokens, feat=_lbl, sort=HANDLESORT,
                            variables=variables)
    args = []
    while tokens[0] != _right_bracket:
        args.append(read_argument(tokens, variables=variables))
    tokens.pop(0)  # we know this is a right bracket
    return ElementaryPredication(pred, label, args=args,
                                 lnk=lnk, surface=surface)


def read_argument(tokens, variables=None):
    """Read and return an Argument."""
    # ARGNAME: (VAR|CONST)
    if variables is None:
        variables = {}
    argname, value = read_featval(tokens, variables=variables)
    return Argument.mrs_argument(argname, value)


def read_lnk(tokens):
    """Read and return a tuple of the pred's lnk type and lnk value,
       if a pred lnk is specified."""
    # < FROM : TO > or < FROM # TO > or < TOK... > or < @ EDGE >
    lnk = None
    if tokens and tokens[0] == _left_angle:
        tokens.pop(0)  # we just checked this is a left angle
        if tokens[0] == _right_angle:
            pass  # empty <> brackets the same as no lnk specified
        # edge lnk: ['@', EDGE, ...]
        elif tokens[0] == _at:
            tokens.pop(0)  # remove the @
            lnk = Lnk.edge(tokens.pop(0))  # edge lnks only have one number
        # character span lnk: [FROM, ':', TO, ...]
        elif tokens[1] == _colon:
            lnk = Lnk.charspan(tokens.pop(0), tokens.pop(1))
            tokens.pop(0)  # this should be the colon
        # chart vertex range lnk: [FROM, '#', TO, ...]
        elif tokens[1] == _hash:
            lnk = Lnk.chartspan(tokens.pop(0), tokens.pop(1))
            tokens.pop(0)  # this should be the hash
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
    if variables is None:
        variables = {}
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
    tokens.pop(0)  # we know this is a right angle
    return hcons

# def read_icons(tokens):
#     # ICONS:<>
#     pass


def unexpected_termination_error():
    raise MrsDecodeError('Invalid MRS: Unexpected termination.')

##############################################################################
##############################################################################
# Encoding


def unset_colors():
    global bold, gray, red, blue, magenta, darkgreen, green, yellow
    bold = gray = red = blue = magenta = darkgreen = green = yellow =\
        lambda x: x


def serialize(ms, version=_default_version, pretty_print=False, color=False):
    """Serialize an MRS structure into a SimpleMRS string."""
    if not color:
        unset_colors()
    delim = '\n' if pretty_print else _default_mrs_delim
    return delim.join(
        serialize_mrs(m, version=version, pretty_print=pretty_print)
        for m in ms
    )


def serialize_mrs(m, version=_default_version, pretty_print=False):
    # note that listed_vars is modified as a side-effect of the lower
    # functions
    listed_vars = set()
    toks = []
    if version >= 1.1:
        if m.lnk is not None:
            toks.append(serialize_lnk(m.lnk))
        if m.surface is not None:
            toks.append('"{}"'.format(m.surface))
    if m.ltop is not None:
        toks += [serialize_argument(_ltop, m.ltop, listed_vars)]
    if m.index is not None:
        toks += [serialize_argument(_index, m.index, listed_vars)]
    #toks = [' '.join(toks)]
    toks += [serialize_rels(m.rels, listed_vars, version=version,
                            pretty_print=pretty_print)]
    toks += [' '.join([serialize_hcons(m.hcons, listed_vars)])]
    delim = ' ' if not pretty_print else '\n  '
    return '{} {} {}'.format(_left_bracket, delim.join(toks), _right_bracket)


def serialize_argument(rargname, value, listed_vars):
    """Serialize an MRS argument into the SimpleMRS format."""
    if isinstance(value, MrsVariable):
        return ' '.join([magenta(rargname) + _colon,
                         serialize_variable(value, listed_vars)])
    else:
        return ' '.join([red(rargname) + _colon, str(value)])


def serialize_variable(var, listed_vars):
    """Serialize an MRS variable, and any variable properties, into the
       SimpleMRS format."""
    if var.sort == HANDLESORT:
        varstr = yellow(bold(str(var)))
    else:
        varstr = blue(bold(str(var)))
    toks = [varstr]
    # only serialize the variable properties if they haven't been already
    if var.vid not in listed_vars and var.properties:
        toks += [_left_bracket, var.sort]
        for propkey, propval in var.properties.items():
            toks += [propkey.upper() + _colon, propval]
        toks += [_right_bracket]
    listed_vars.add(var.vid)
    return ' '.join(toks)


def serialize_rels(rels, listed_vars, version=_default_version,
                   pretty_print=False):
    """Serialize a RELS list of EPs into the SimpleMRS encoding."""
    delim = ' ' if not pretty_print else '\n          '
    string = ' '.join([_rels + _colon, _left_angle])
    string += ' ' + delim.join(serialize_ep(ep, listed_vars, version=version)
                               for ep in rels)
    string += ' ' + _right_angle
    return string


def serialize_ep(ep, listed_vars, version=_default_version):
    """Serialize an Elementary Predication into the SimpleMRS encoding."""
    toks = [_left_bracket]
    if ep.is_quantifier():
        predstr = darkgreen(ep.pred.string)
    else:
        predstr = green(bold(ep.pred.string))
    toks += [predstr + serialize_lnk(ep.lnk)]
    if version >= 1.1:
        if ep.surface is not None:
            toks.append('"{}"'.format(ep.surface))
    toks += [serialize_argument(_lbl, ep.label, listed_vars)]
    # if ep.iv is not None:
    #     toks += [serialize_argument(IVARG_ROLE, ep.iv, listed_vars)]
    for arg in ep.args:
        toks += [serialize_argument(arg.argname, arg.value, listed_vars)]
    # add the constant if it exists (currently done as a regular arg above)
    # if ep.carg is not None:
    #     toks += [serialize_const(CONSTARG, ep.carg)]
    toks += [_right_bracket]
    return ' '.join(toks)


def serialize_lnk(lnk):
    """Serialize a predication lnk to surface form into the SimpleMRS
       encoding."""
    s = ""
    if lnk is not None:
        s = _left_angle
        if lnk.type == Lnk.CHARSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), _colon, str(cto)])
        elif lnk.type == Lnk.CHARTSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), _hash, str(cto)])
        elif lnk.type == Lnk.TOKENS:
            s += ' '.join([str(t) for t in lnk.data])
        elif lnk.type == Lnk.EDGE:
            s += ''.join([_at, str(lnk.data)])
        s += _right_angle
    return gray(s)


def serialize_hcons(hcons, listed_vars):
    """Serialize a Handle Constraint into the SimpleMRS encoding."""
    toks = [_hcons + _colon, _left_angle]
    for hcon in hcons:
        if hcon.relation == QEQ:
            rel = _qeq
        elif hcon.relation == LHEQ:
            rel = _lheq
        elif hcon.relation == OUTSCOPES:
            rel = _outscopes
        toks += [serialize_variable(hcon.hi, listed_vars),
                 rel,
                 serialize_variable(hcon.lo, listed_vars)]
    toks += [_right_angle]
    return ' '.join(toks)
