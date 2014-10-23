
# SimpleMRS codec
# Summary: This module implements serialization and deserialization of
#          the SimpleMRS encoding of Minimal Recusion Semantics. It
#          provides the standard Pickle API calls of load, loads, dump,
#          and dumps.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict, deque
import re
from delphin.mrs import Mrs
from delphin.mrs.components import (
    Hook, ElementaryPredication, Argument, Pred,
    MrsVariable, Lnk, HandleConstraint, IndividualConstraint
)
from delphin.mrs.config import (HANDLESORT, QEQ, LHEQ, OUTSCOPES)
from delphin.mrs.util import ReadOnceDict
from delphin._exceptions import XmrsDeserializationError as XDE

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
_top = r'TOP'
_ltop = r'LTOP'
_index = r'INDEX'
_rels = r'RELS'
_hcons = r'HCONS'
_icons = r'ICONS'
_lbl = r'LBL'
# possible relations for handle constraints
_qeq = r'qeq'
_lheq = r'lheq'
_outscopes = r'outscopes'
_valid_hcons = [_qeq, _lheq, _outscopes]

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
    return deque(tokenizer.findall(string))


def validate_token(token, expected):
    """Make sure the given token is as expected, or raise an error. This
       comparison is case insensitive."""
    # uppercase the input, since expected tokens are all upper case
    if token.upper() != expected:
        invalid_token_error(token, expected)


def validate_tokens(tokens, expected):
    for exp_tok in expected:
        validate_token(tokens.popleft(), exp_tok)


def is_variable(token):
    try:
        MrsVariable.sort_vid_split(token)
        return True
    except ValueError:
        return False


def invalid_token_error(token, expected):
    raise XDE('Invalid token: "{}"\tExpected: "{}"'.format(token, expected))


def deserialize(string):
    # FIXME: consider buffering this so we don't read the whole string at once
    tokens = tokenize(string)
    while tokens:
        yield read_mrs(tokens)


def read_mrs(tokens, version=_default_version):
    """Decode a sequence of Simple-MRS tokens. Assume LTOP, INDEX, RELS,
       HCONS, and ICONS occur in that order."""
    # variables needs to be passed to any function that can call read_variable
    variables = {}
    # [ LTOP : handle INDEX : variable RELS : rels-list HCONS : hcons-list ]
    try:
        validate_token(tokens.popleft(), _left_bracket)
        ltop = index = surface = lnk = None
        # SimpleMRS extension for encoding surface string
        if tokens[0] == _left_angle:
            lnk = read_lnk(tokens)
        if tokens[0].startswith('"'): # and tokens[0].endswith('"'):
            surface = tokens.popleft()[1:-1] # get rid of first quotes
        if tokens[0] in (_ltop, _top):
            _, ltop = read_featval(tokens, variables=variables)
        if tokens[0] == _index:
            _, index = read_featval(tokens, feat=_index, variables=variables)
        rels = read_rels(tokens, variables=variables)
        hcons = read_hcons(tokens, variables=variables)
        icons = read_icons(tokens, variables=variables)
        validate_token(tokens.popleft(), _right_bracket)
        m = Mrs(hook=Hook(ltop=ltop, index=index),
                rels=rels,
                hcons=hcons,
                icons=icons,
                lnk=lnk,
                surface=surface)
    except IndexError:
        unexpected_termination_error()
    return m


def read_featval(tokens, feat=None, sort=None, variables=None):
    # FEAT : (var-or-handle|const)
    if variables is None:
        variables = {}
    name = tokens.popleft()
    if feat is not None:
        validate_token(name, feat)
    validate_token(tokens.popleft(), _colon)
    # if it's not a variable, assume it's a constant
    if is_variable(tokens[0]):
        value = read_variable(tokens, sort=sort, variables=variables)
    else:
        value = tokens.popleft()
    return name, value


def read_variable(tokens, sort=None, variables=None):
    """Read and return the MrsVariable object for the value of the
       variable. Fail if the sort does not match the expected."""
    # var [ vartype PROP : val ... ]
    if variables is None:
        variables = {}
    var = tokens.popleft()
    srt, vid = MrsVariable.sort_vid_split(var)
    # consider something like not(srt <= sort) in the case of subsumptive sorts
    if sort is not None and srt != sort:
        raise XDE('Variable {} has sort "{}", expected "{}"'
                  .format(var, srt, sort))
    vartype, props = read_props(tokens)
    if vartype is not None and srt != vartype:
        raise XDE('Variable "{}" and its cvarsort "{}" are not the same.'
                  .format(var, vartype))
    if srt == 'h' and props:
        raise XDE('Handle variable "{}" has a non-empty property set {}.'
                  .format(var, props))
    if vid in variables:
        if srt != variables[vid].sort:
            raise XDE('Variable {} has a conflicting sort with {}'
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
    tokens.popleft()  # get rid of bracket (we just checked it)
    vartype = tokens.popleft()
    # check if a vartype wasn't given (next token is : )
    if tokens[0] == _colon:
        invalid_token_error(vartype, "variable type")
    while tokens[0] != _right_bracket:
        prop = tokens.popleft()
        validate_token(tokens.popleft(), _colon)
        val = tokens.popleft()
        props[prop] = val
    tokens.popleft()  # we know this is a right bracket
    return vartype, props


def read_rels(tokens, variables=None):
    """Read and return a RELS set of ElementaryPredications."""
    # RELS: < ep* >
    if tokens[0] != _rels:
        return None
    tokens.popleft()  # pop "RELS"
    if variables is None:
        variables = {}
    rels = []
    validate_tokens(tokens, [_colon, _left_angle])
    while tokens[0] != _right_angle:
        rels += [read_ep(tokens, variables=variables)]
    tokens.popleft()  # we know this is a right angle
    return rels


def read_ep(tokens, variables=None):
    """Read and return an ElementaryPredication."""
    # [ pred LBL : lbl ARG : variable-or-handle ... ]
    # or [ pred < lnk > ...
    if variables is None:
        variables = {}
    validate_token(tokens.popleft(), _left_bracket)
    pred = Pred.string_or_grammar_pred(tokens.popleft())
    lnk = read_lnk(tokens)
    if tokens[0].startswith('"'):
        surface = tokens.popleft()[1:-1] # get rid of first quotes
    else:
        surface = None
    _, label = read_featval(tokens, feat=_lbl, sort=HANDLESORT,
                            variables=variables)
    args = []
    while tokens[0] != _right_bracket:
        args.append(read_argument(tokens, variables=variables))
    tokens.popleft()  # we know this is a right bracket
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
    if tokens[0] == _left_angle:
        tokens.popleft()  # we just checked this is a left angle
        if tokens[0] == _right_angle:
            pass  # empty <> brackets the same as no lnk specified
        # edge lnk: ['@', EDGE, ...]
        elif tokens[0] == _at:
            tokens.popleft()  # remove the @
            lnk = Lnk.edge(tokens.popleft())  # edge lnks only have one number
        # character span lnk: [FROM, ':', TO, ...]
        elif tokens[1] == _colon:
            lnk = Lnk.charspan(tokens.popleft(), tokens[1])
            tokens.popleft()  # this should be the colon
            tokens.popleft()  # and this is the cto
        # chart vertex range lnk: [FROM, '#', TO, ...]
        elif tokens[1] == _hash:
            lnk = Lnk.chartspan(tokens.popleft(), tokens[1])
            tokens.popleft()  # this should be the hash
            tokens.popleft()  # and this is the to vertex
        # tokens lnk: [(TOK,)+ ...]
        else:
            lnkdata = []
            while tokens[0] != _right_angle:
                lnkdata.append(int(tokens.popleft()))
            lnk = Lnk.tokens(lnkdata)
        validate_token(tokens.popleft(), _right_angle)
    return lnk


def read_hcons(tokens, variables=None):
    # HCONS:< HANDLE (qeq|lheq|outscopes) HANDLE ... >
    """Read and return an HCONS list."""
    if tokens[0] != _hcons:
        return None
    tokens.popleft()  # pop "HCONS"
    if variables is None:
        variables = {}
    hcons = []
    validate_tokens(tokens, [_colon, _left_angle])
    while tokens[0] != _right_angle:
        hi = read_variable(tokens, sort='h', variables=variables)
        # rels are case-insensitive and the convention is lower-case
        rel = tokens.popleft().lower()
        if rel == _qeq:
            rel = QEQ
        elif rel == _lheq:
            rel = LHEQ
        elif rel == _outscopes:
            rel = OUTSCOPES
        else:
            invalid_token_error(rel, '('+'|'.join(_valid_hcons)+')')
        lo = read_variable(tokens, sort='h', variables=variables)
        hcons.append(HandleConstraint(hi, rel, lo))
    tokens.popleft()  # we know this is a right angle
    return hcons

def read_icons(tokens, variables=None):
    # ICONS:< TARGET RELATION CLAUSE ... >
    if tokens[0] != _icons:
        return None
    tokens.popleft()  # pop "ICONS"
    if variables is None:
        variables = {}
    icons = []
    validate_tokens(tokens, [_colon, _left_angle])
    while tokens[0] != _right_angle:
        target = read_variable(tokens, variables=variables)
        relation = tokens.popleft().lower()
        clause = read_variable(tokens, variables=variables)
        icons.append(IndividualConstraint(target, relation, clause))
    tokens.popleft()  # we know this is a right angle
    return icons


def unexpected_termination_error():
    raise XDE('Invalid MRS: Unexpected termination.')

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
    g = m._graph
    varprops = ReadOnceDict((v.vid, v.properties) for v in g.nodes()
                            if isinstance(v, MrsVariable))
    listed_vars = set()
    toks = []
    if version >= 1.1:
        if m.lnk is not None:
            toks.append(serialize_lnk(m.lnk))
        if m.surface is not None:
            toks.append('"{}"'.format(m.surface))
    if m.ltop is not None:
        toks.append(serialize_argument(
            _top if version >= 1.1 else _ltop, m.ltop, varprops
        ))
    if m.index is not None:
        toks.append(serialize_argument(
            _index, m.index, varprops
        ))
    delim = ' ' if not pretty_print else '\n          '
    toks.append('RELS: < {eps} >'.format(
        eps=delim.join(serialize_ep(g, nid, varprops, version=version)
                       for nid in g.nodeids)
    ))
    #if len(g.nodeids) is not None:
    #    toks += [serialize_rels(g, listed_vars, version=version,
    #                            pretty_print=pretty_print)]
    if m.hcons is not None:
        toks += [' '.join([serialize_hcons(m.hcons, listed_vars)])]
    if version >= 1.1 and m.icons:  # `is not None` if you want "ICONS: < >""
        toks += [' '.join([serialize_icons(m.icons, listed_vars)])]        
    delim = ' ' if not pretty_print else '\n  '
    return '{} {} {}'.format(_left_bracket, delim.join(toks), _right_bracket)


def serialize_argument(rargname, value, varprops):
    """Serialize an MRS argument into the SimpleMRS format."""
    _argument = '{rargname}: {value}{props}'
    if isinstance(value, MrsVariable):
        props = varprops.get(value.vid, {})
        var = bold(str(value))
        return _argument.format(
            rargname=magenta(rargname),
            value=yellow(var) if value.sort == HANDLESORT else blue(var),
            props='' if not props else ' [ {} ]'.format(
                ' '.join(map('{0[0]}: {0[1]}'.format, props.items())))
        )
    else:
        return _argument.format(
            rargname=red(rargname),
            value=str(value),
            props=''
        )


def serialize_ep(g, nid, varprops, version=_default_version):
    """Serialize an Elementary Predication into the SimpleMRS encoding."""
    node = g.node[nid]
    arglist = ' '.join([serialize_argument(rarg, val, varprops)
                        for rarg, val in node['rargs'].items()])
    surface = None if version < 1.1 else node['surface']
    pred = node['pred']
    predstr = pred.string 
    return '[ {pred}{lnk}{surface} LBL: {label}{s}{args} ]'.format(
        pred=darkgreen(predstr) if pred.is_quantifier() else green(predstr),
        lnk=serialize_lnk(node['lnk']),
        surface=' "{}"'.format(surface) if surface is not None else '',
        label=yellow(bold(str(node['label']))),
        s=' ' if arglist else '',
        args=arglist
    )


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
    """Serialize |HandleConstraints| into the SimpleMRS encoding."""
    toks = [_hcons + _colon, _left_angle]
    for hcon in hcons:
        if hcon.relation == QEQ:
            rel = _qeq
        elif hcon.relation == LHEQ:
            rel = _lheq
        elif hcon.relation == OUTSCOPES:
            rel = _outscopes
        toks += [yellow(bold(str(hcon.hi))), rel, yellow(bold(str(hcon.lo)))]
    toks += [_right_angle]
    return ' '.join(toks)

def serialize_icons(icons, listed_vars):
    """Serialize |IndividualConstraints| into the SimpleMRS encoding."""
    toks = [_icons + _colon, _left_angle]
    for icon in icons:
        toks += [blue(bold(str(icon.target))),
                 icon.relation,
                 blue(bold(str(icon.clause)))]
    toks += [_right_angle]
    return ' '.join(toks)