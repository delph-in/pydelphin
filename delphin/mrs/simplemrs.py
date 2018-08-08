
"""
Serialization functions for the SimpleMRS format.
"""


# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function

from collections import deque, defaultdict
import re
from warnings import warn

from delphin.util import stringtypes
from delphin.mrs import Mrs
from delphin.mrs.components import (
    ElementaryPredication, Pred, Lnk, HandleConstraint, IndividualConstraint,
    sort_vid_split, var_sort, var_re, hcons, icons
)
from delphin.mrs.config import (HANDLESORT, CONSTARG_ROLE)
from delphin.mrs.util import rargname_sortkey
from delphin.exceptions import (
    XmrsDeserializationError as XDE,
    XmrsError,
    XmrsWarning
)

try:
    from pygments import highlight as highlight_
    from pygments.formatters import TerminalFormatter
    from delphin.extra.highlight import SimpleMrsLexer, mrs_colorscheme
    lexer = SimpleMrsLexer()
    formatter = TerminalFormatter(bg='dark', colorscheme=mrs_colorscheme)
    def highlight(text):
        return highlight_(text, lexer, formatter)
except ImportError:
    # warnings.warn
    def highlight(text):
        return text

# versions are:
#  * 1.0 long running standard
#  * 1.1 added support for MRS-level lnk, surface and EP-level surface
_default_version = 1.1
_latest_version = 1.1

_valid_hcons = ['qeq', 'lheq', 'outscopes']

# pretty-print options
_default_mrs_delim = '\n'

##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False, version=_default_version,
         strict=False, errors='warn'):
    """
    Deserialize SimpleMRSs from a file (handle or filename)

    Args:
        fh (str, file): input filename or file object
        single: if `True`, only return the first read Xmrs object
        strict: deprecated; a `True` value is the same as
            `errors='strict'`, and a `False` value is the same as
            `errors='warn'`
        errors: if `'strict'`, ill-formed MRSs raise an error; if
            `'warn'`, raise a warning instead; if `'ignore'`, do not
            warn or raise errors for ill-formed MRSs
    Returns:
        a generator of Xmrs objects (unless the *single* option is
        `True`)
    """
    if isinstance(fh, stringtypes):
        s = open(fh, 'r').read()
    else:
        s = fh.read()
    return loads(s, single=single, version=version,
                 strict=strict, errors=errors)


def loads(s, single=False, version=_default_version,
          strict=False, errors='warn'):
    """
    Deserialize SimpleMRS string representations

    Args:
        s (str): a SimpleMRS string
        single (bool): if `True`, only return the first Xmrs object
    Returns:
        a generator of Xmrs objects (unless *single* is `True`)
    """
    ms = deserialize(s, version=version, strict=strict, errors=errors)
    if single:
        return next(ms)
    else:
        return ms


def dump(destination, ms, single=False, version=_default_version, properties=True,
         pretty_print=False, color=False, **kwargs):
    """
    Serialize Xmrs objects to SimpleMRS and write to a file

    Args:
        destination: filename or file object where data will be written
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object
            instead of as an iterator
        properties: if `False`, suppress variable properties
        pretty_print: if `True`, add newlines and indentation
        color: if `True`, colorize the output with ANSI color codes
    """
    text = dumps(ms,
                 single=single,
                 version=version,
                 properties=properties,
                 pretty_print=pretty_print,
                 color=color,
                 **kwargs)

    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w') as fh:
            print(text, file=fh)


def dumps(ms, single=False, version=_default_version, properties=True,
          pretty_print=False, color=False, **kwargs):
    """
    Serialize an Xmrs object to a SimpleMRS representation

    Args:
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object instead
            of as an iterator
        properties: if `False`, suppress variable properties
        pretty_print: if `True`, add newlines and indentation
        color: if `True`, colorize the output with ANSI color codes
    Returns:
        a SimpleMrs string representation of a corpus of Xmrs
    """
    if not pretty_print and kwargs.get('indent'):
        pretty_print = True
    if single:
        ms = [ms]
    return serialize(ms, version=version, properties=properties,
                     pretty_print=pretty_print, color=color)


# for convenience

load_one = lambda fh, **kwargs: load(fh, single=True, **kwargs)
loads_one = lambda s, **kwargs: loads(s, single=True, **kwargs)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Deserialization

# The _tokenizer has 3 sub-regexen:
#   the first is for strings (e.g. "_dog_n_rel", "\"quoted string\"")
#   the second looks for unquoted type preds (lookahead for space or lnk)
#   the second is for args, variables, preds, etc (e.g. ARG1, _dog_n_rel, x4)
#   the last is for contentful punctuation (e.g. [ ] < > : # @)

_tokenizer = re.compile(r'("[^"\\]*(?:\\.[^"\\]*)*"'
                       r'|_(?:[^ \n<]|<(?![-0-9:#@ ]*>))*'
                       r'|[^ \n:#@\[\]"<>]+'
                       r'|[:#@\[\]<>])')


def tokenize(string):
    """Split the SimpleMrs string into tokens."""
    return deque(_tokenizer.findall(string))


def _invalid_token_error(token, expected):
    raise XDE('Invalid token: "{}"\tExpected: "{}"'.format(token, expected))


def deserialize(string, version=_default_version, strict=True, errors='warn'):
    if strict:
        warnings.warn(
            'strict=True parameter is deprecated; use errors=\'strict\'',
            DeprecationWarning
        )
        errors = 'strict'
    # FIXME: consider buffering this so we don't read the whole string at once
    tokens = tokenize(string)
    while tokens:
        yield _read_mrs(tokens, version, errors)


def _read_literals(tokens, *toks):
    for tok in toks:
        token = tokens.popleft()
        if token != tok:
            raise XDE(
                'Expected \'{}\': {}'.format(tok, ' '.join(list(tokens)))
            )


def _read_mrs(tokens, version, errors):
    #return read_mrs(tokens)
    try:
        _read_literals(tokens, '[')
        top = idx = surface = lnk = None
        vars_ = {}
        if version >= 1.1:
            if tokens[0] == '<':
                lnk = _read_lnk(tokens)
            if tokens[0].startswith('"'):  # and tokens[0].endswith('"'):
                surface = tokens.popleft()[1:-1]  # get rid of first quotes
        if tokens[0].upper() in ('LTOP', 'TOP'):
            tokens.popleft()  # LTOP / TOP
            _read_literals(tokens, ':')
            top = tokens.popleft()
            vars_[top] = []
        if tokens[0].upper() == 'INDEX':
            tokens.popleft()  # INDEX
            _read_literals(tokens, ':')
            idx = tokens.popleft()
            vars_[idx] = _read_props(tokens)
        rels = _read_rels(tokens, vars_)
        hcons = _read_cons(tokens, 'HCONS', vars_)
        icons = _read_cons(tokens, 'ICONS', vars_)
        _read_literals(tokens, ']')
        # at this point, we could uniquify proplists in vars_, but most
        # likely it isn't necessary, and might harm things if we
        # leave potential dupes in there. let's see how it plays out.
        m = Mrs(top=top, index=idx, rels=rels,
                hcons=hcons, icons=icons,
                lnk=lnk, surface=surface, vars=vars_)
    except IndexError:
        _unexpected_termination_error()
    if errors != 'ignore':
        try:
            m.validate()
        except XmrsError as ex:
            if errors == 'warn':
                warn(str(ex), XmrsWarning)
            elif errors == 'strict':
                raise
    return m


def _read_props(tokens):
    props = []
    if tokens[0] == '[':
        tokens.popleft()  # [
        vartype = tokens.popleft()  # this gets discarded though
        while tokens[0] != ']':
            key = tokens.popleft()
            _read_literals(tokens, ':')
            val = tokens.popleft()
            props.append((key, val))
        tokens.popleft()  # ]
    return props


def _read_rels(tokens, vars_):
    rels = None
    nid = 10000
    if tokens[0].upper() == 'RELS':
        rels = []
        tokens.popleft()  # RELS
        _read_literals(tokens, ':', '<')
        while tokens[0] != '>':
            rels.append(_read_ep(tokens, nid, vars_))
            nid += 1
        tokens.popleft()  # >
    return rels


def _read_ep(tokens, nid, vars_):
    # reassign these locally to avoid global lookup
    CARG = CONSTARG_ROLE
    _var_re = var_re
    # begin parsing
    _read_literals(tokens, '[')
    pred = Pred.surface_or_abstract(tokens.popleft())
    lnk = _read_lnk(tokens)
    surface = label = None
    if tokens[0].startswith('"'):
        surface = tokens.popleft()[1:-1]  # get rid of first quotes
    if tokens[0].upper() == 'LBL':
        tokens.popleft()  # LBL
        _read_literals(tokens, ':')
        label = tokens.popleft()
        vars_[label] = []
    args = {}
    while tokens[0] != ']':
        role = tokens.popleft().upper()
        _read_literals(tokens, ':')
        val = tokens.popleft()
        if role.upper() == CARG:
            if val and (val[0], val[-1]) == ('"', '"'):
                val = val[1:-1]
        elif _var_re.match(val) is not None:
            props = _read_props(tokens)
            if val not in vars_:
                vars_[val] = []
            vars_[val].extend(props)
        args[role] = val
    tokens.popleft()  # ]
    return ElementaryPredication(nid, pred, label, args, lnk, surface)


def _read_cons(tokens, constype, vars_):
    cons = None
    if tokens[0].upper() == constype:
        cons = []
        tokens.popleft()  # (H|I)CONS
        _read_literals(tokens, ':', '<')
        while tokens[0] != '>':
            left = tokens.popleft()
            lprops = _read_props(tokens)
            reln = tokens.popleft().lower()
            rght = tokens.popleft()
            rprops = _read_props(tokens)
            cons.append((left, reln, rght))
            # update properties
            if left not in vars_: vars_[left] = []
            vars_[left].extend(lprops)
            if rght not in vars_: vars_[rght] = []
            vars_[rght].extend(lprops)
        tokens.popleft()  # >
    return cons


def _read_lnk(tokens):
    """Read and return a tuple of the pred's lnk type and lnk value,
       if a pred lnk is specified."""
    # < FROM : TO > or < FROM # TO > or < TOK... > or < @ EDGE >
    lnk = None
    if tokens[0] == '<':
        tokens.popleft()  # we just checked this is a left angle
        if tokens[0] == '>':
            pass  # empty <> brackets the same as no lnk specified
        # edge lnk: ['@', EDGE, ...]
        elif tokens[0] == '@':
            tokens.popleft()  # remove the @
            lnk = Lnk.edge(tokens.popleft())  # edge lnks only have one number
        # character span lnk: [FROM, ':', TO, ...]
        elif tokens[1] == ':':
            lnk = Lnk.charspan(tokens.popleft(), tokens[1])
            tokens.popleft()  # this should be the colon
            tokens.popleft()  # and this is the cto
        # chart vertex range lnk: [FROM, '#', TO, ...]
        elif tokens[1] == '#':
            lnk = Lnk.chartspan(tokens.popleft(), tokens[1])
            tokens.popleft()  # this should be the hash
            tokens.popleft()  # and this is the to vertex
        # tokens lnk: [(TOK,)+ ...]
        else:
            lnkdata = []
            while tokens[0] != '>':
                lnkdata.append(int(tokens.popleft()))
            lnk = Lnk.tokens(lnkdata)
        _read_literals(tokens, '>')
    return lnk


def _unexpected_termination_error():
    raise XDE('Invalid MRS: Unexpected termination.')

##############################################################################
##############################################################################
# Encoding


def serialize(ms, version=_default_version, properties=True,
              pretty_print=False, color=False):
    """Serialize an MRS structure into a SimpleMRS string."""
    delim = '\n' if pretty_print else _default_mrs_delim
    output = delim.join(
        _serialize_mrs(m, properties=properties,
                       version=version, pretty_print=pretty_print)
        for m in ms
    )
    if color:
        output = highlight(output)
    return output


def _serialize_mrs(m, properties, version=_default_version, pretty_print=False):
    # note that varprops is modified as a side-effect of the lower
    # functions
    if properties:
        varprops = {v: d['props'] for v, d in m._vars.items() if d['props']}
    else:
        varprops = {}
    toks = []
    if version >= 1.1:
        header_toks = []
        if m.lnk is not None and m.lnk.data != (-1, -1):  # don't do <-1:-1>
            header_toks.append(_serialize_lnk(m.lnk))
        if m.surface is not None:
            header_toks.append('"{}"'.format(m.surface))
        if header_toks:
            toks.append(' '.join(header_toks))
    if m.top is not None:
        toks.append(_serialize_argument(
            'TOP' if version >= 1.1 else 'LTOP', m.top, varprops
        ))
    if m.index is not None:
        toks.append(_serialize_argument(
            'INDEX', m.index, varprops
        ))
    delim = ' ' if not pretty_print else '\n          '
    toks.append('RELS: < {eps} >'.format(
        eps=delim.join(_serialize_ep(ep, varprops, version=version)
                       for ep in m.eps())
    ))
    toks += [_serialize_hcons(hcons(m))]
    icons_ = icons(m)
    if icons_:  # make unconditional for "ICONS: < >"
        toks += [_serialize_icons(icons_)]
    delim = ' ' if not pretty_print else '\n  '
    return '{} {} {}'.format('[', delim.join(toks), ']')


def _serialize_argument(rargname, value, varprops):
    """Serialize an MRS argument into the SimpleMRS format."""
    _argument = '{rargname}: {value}{props}'
    if rargname == CONSTARG_ROLE:
        value = '"{}"'.format(value)
    props = ''
    if value in varprops:
        props = ' [ {} ]'.format(
            ' '.join(
                [var_sort(value)] +
                list(map('{0[0]}: {0[1]}'.format,
                         [(k.upper(), v) for k, v in varprops[value]]))
            )
        )
        del varprops[value]  # only print props once
    return _argument.format(
        rargname=rargname,
        value=str(value),
        props=props
    )


def _serialize_ep(ep, varprops, version=_default_version):
    """Serialize an Elementary Predication into the SimpleMRS encoding."""
    # ('nodeid', 'pred', 'label', 'args', 'lnk', 'surface', 'base')
    args = ep[3]
    arglist = ' '.join([_serialize_argument(rarg, args[rarg], varprops)
                        for rarg in sorted(args, key=rargname_sortkey)])
    if version < 1.1 or len(ep) < 6 or ep[5] is None:
        surface = ''
    else:
        surface = ' "%s"' % ep[5]
    lnk = None if len(ep) < 5 else ep[4]
    pred = ep[1]
    predstr = pred.string
    return '[ {pred}{lnk}{surface} LBL: {label}{s}{args} ]'.format(
        pred=predstr,
        lnk=_serialize_lnk(lnk),
        surface=surface,
        label=str(ep[2]),
        s=' ' if arglist else '',
        args=arglist
    )


def _serialize_lnk(lnk):
    """Serialize a predication lnk to surface form into the SimpleMRS
       encoding."""
    s = ""
    if lnk is not None:
        s = '<'
        if lnk.type == Lnk.CHARSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), ':', str(cto)])
        elif lnk.type == Lnk.CHARTSPAN:
            cfrom, cto = lnk.data
            s += ''.join([str(cfrom), '#', str(cto)])
        elif lnk.type == Lnk.TOKENS:
            s += ' '.join([str(t) for t in lnk.data])
        elif lnk.type == Lnk.EDGE:
            s += ''.join(['@', str(lnk.data)])
        s += '>'
    return s


def _serialize_hcons(hcons):
    """Serialize [HandleConstraints] into the SimpleMRS encoding."""
    toks = ['HCONS:', '<']
    for hc in hcons:
        toks.extend(hc)
        # reln = hcon[1]
        # toks += [hcon[0], rel, str(hcon.lo)]
    toks += ['>']
    return ' '.join(toks)


def _serialize_icons(icons):
    """Serialize [IndividualConstraints] into the SimpleMRS encoding."""
    toks = ['ICONS:', '<']
    for ic in icons:
        toks.extend(ic)
        # toks += [str(icon.left),
        #          icon.relation,
        #          str(icon.right)]
    toks += ['>']
    return ' '.join(toks)
