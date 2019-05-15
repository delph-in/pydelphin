
"""
Serialization for the Indexed MRS format.

The Indexed MRS format does not include role names such as `ARG1`,
`ARG2`, etc., so the order of the arguments in a predication is
important. For this reason, serialization with the Indexed MRS format
requires the use of a SEM-I (see the :mod:`delphin.semi` module).

Example:

* *The new chef whose soup accidentally spilled quit and left.*

::

  < h0, e2:PROP:PAST:INDICATIVE:-:-,
    { h4:_the_q<0:3>(x3:3:SG:GENDER:+:PT, h5, h6),
      h7:_new_a_1<4:7>(e8:PROP:UNTENSED:INDICATIVE:BOOL:-, x3),
      h7:_chef_n_1<8:12>(x3),
      h9:def_explicit_q<13:18>(x10:3:SG:GENDER:BOOL:PT, h11, h12),
      h13:poss<13:18>(e14:PROP:UNTENSED:INDICATIVE:-:-, x10, x3),
      h13:_soup_n_1<19:23>(x10),
      h7:_accidental_a_1<24:36>(e15:PROP:UNTENSED:INDICATIVE:-:-, e16:PROP:PAST:INDICATIVE:-:-),
      h7:_spill_v_1<37:44>(e16, x10, i17),
      h1:_quit_v_1<45:49>(e18:PROP:PAST:INDICATIVE:-:-, x3, i19),
      h1:_and_c<50:53>(e2, e18, e20:PROP:PAST:INDICATIVE:-:-),
      h1:_leave_v_1<54:59>(e20, x3, i21) },
    { h0 qeq h1,
      h5 qeq h7,
      h11 qeq h13 } >
"""  # noqa: E501

from pathlib import Path

from delphin.lnk import Lnk
from delphin.mrs import (
    MRS,
    EP,
    HCons,
    ICons,
    CONSTANT_ROLE)
from delphin import variable
from delphin.mrs import MRSSyntaxError
from delphin.util import Lexer


CODEC_INFO = {
    'representation': 'mrs',
}


##############################################################################
##############################################################################
# Pickle-API methods

def load(source, semi):
    """
    Deserialize Indexed MRS from a file (handle or filename)

    Args:
        source (str, file): input filename or file object
        semi (:class:`SemI`): the semantic interface for the grammar
            that produced the MRS
    Returns:
        a list of MRS objects
    """
    if hasattr(source, 'read'):
        ms = list(_decode(source, semi))
    else:
        source = Path(source).expanduser()
        with source.open() as fh:
            ms = list(_decode(fh, semi))
    return ms


def loads(s, semi, single=False, encoding='utf-8'):
    """
    Deserialize Indexed MRS string representations

    Args:
        s (str): an Indexed MRS string
        semi (:class:`SemI`): the semantic interface for the grammar
            that produced the MRS
    Returns:
        a list of MRS objects
    """
    ms = list(_decode(s.splitlines(), semi))
    return ms


def dump(ms, destination, semi, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize MRS objects to Indexed MRS and write to a file

    Args:
        ms: an iterator of MRS objects to serialize
        destination: filename or file object where data will be written
        semi (:class:`SemI`): the semantic interface for the grammar
            that produced the MRS
        properties: if `False`, suppress morphosemantic properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ms, semi, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ms, semi, properties=True, lnk=True, indent=False):
    """
    Serialize MRS objects to an Indexed MRS representation

    Args:
        ms: an iterator of MRS objects to serialize
        semi (:class:`SemI`): the semantic interface for the grammar
            that produced the MRS
        properties: if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        an Indexed MRS string representation of a corpus of MRS objects
    """
    return _encode(ms, semi, properties, lnk, indent)


def decode(s, semi):
    """
    Deserialize a MRS object from an Indexed MRS string.

    Args:
        s (str): an Indexed MRS string
        semi (:class:`SemI`): the semantic interface for the grammar
            that produced the MRS
    """
    lexer = _IndexedMRSLexer.lex(s.splitlines())
    return _decode_indexed(lexer, semi)


def encode(d, semi, properties=True, lnk=True, indent=False):
    """
    Serialize a MRS object to an Indexed MRS string.

    Args:
        d: a MRS object
        semi (:class:`SemI`): the semantic interface for the grammar
            that produced the MRS
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        an Indexed MRS-serialization of the MRS object
    """
    return _encode_indexed(d, semi, properties, lnk, indent)


##############################################################################
##############################################################################
# Decoding

_IndexedMRSLexer = Lexer(
    tokens=[
        (r'<-?\d+:-?\d+>', 'LNK:a lnk value'),
        (r'"([^"\\]*(?:\\.[^"\\]*)*)"', 'DQSTRING:a string'),
        (r'<', 'LANGLE:<'),
        (r'>', 'RANGLE:>'),
        (r'\{', 'LBRACE:{'),
        (r'\}', 'RBRACE:}'),
        (r'\(', 'LPAREN:('),
        (r'\)', 'RPAREN:)'),
        (r',', 'COMMA:,'),
        (r':', 'COLON::'),
        (r'[^\s"\'()\/,:;<=>[\]{}]+', 'SYMBOL:a symbol'),
        (r'[^\s]', 'UNEXPECTED')
    ],
    error_class=MRSSyntaxError)

LNK      = _IndexedMRSLexer.tokentypes.LNK
DQSTRING = _IndexedMRSLexer.tokentypes.DQSTRING
LANGLE   = _IndexedMRSLexer.tokentypes.LANGLE
RANGLE   = _IndexedMRSLexer.tokentypes.RANGLE
LBRACE   = _IndexedMRSLexer.tokentypes.LBRACE
RBRACE   = _IndexedMRSLexer.tokentypes.RBRACE
LPAREN   = _IndexedMRSLexer.tokentypes.LPAREN
RPAREN   = _IndexedMRSLexer.tokentypes.RPAREN
COMMA    = _IndexedMRSLexer.tokentypes.COMMA
COLON    = _IndexedMRSLexer.tokentypes.COLON
SYMBOL   = _IndexedMRSLexer.tokentypes.SYMBOL


def _decode(lineiter, semi):
    lexer = _IndexedMRSLexer.lex(lineiter)
    try:
        while lexer.peek():
            yield _decode_indexed(lexer, semi)
    except StopIteration:
        pass


def _decode_indexed(lexer, semi):
    icons = lnk = surface = identifier = None
    variables = {}
    lexer.expect_type(LANGLE)
    top, _, index = lexer.expect_type(SYMBOL, COMMA, SYMBOL)
    if lexer.accept_type(COLON):
        variables[index] = _decode_proplist(lexer)
    lexer.expect_type(COMMA)
    rels = _decode_rels(lexer, variables, semi)
    hcons = _decode_cons(lexer, HCons)
    if lexer.accept_type(COMMA):
        icons = _decode_cons(lexer, ICons)
    lexer.expect_type(RANGLE)
    _match_properties(variables, semi)
    return MRS(top=top,
               index=index,
               rels=rels,
               hcons=hcons,
               icons=icons,
               variables=variables,
               lnk=lnk,
               surface=surface,
               identifier=identifier)


def _decode_proplist(lexer):
    proplist = [lexer.expect_type(SYMBOL)]
    while lexer.accept_type(COLON):
        propval = lexer.expect_type(SYMBOL)
        proplist.append(propval)
    return proplist


def _decode_rels(lexer, variables, semi):
    rels = []
    lexer.expect_type(LBRACE)
    if lexer.peek()[0] != RBRACE:
        while True:
            rels.append(_decode_rel(lexer, variables, semi))
            if not lexer.accept_type(COMMA):
                break
    lexer.expect_type(RBRACE, COMMA)
    return rels


def _decode_rel(lexer, variables, semi):
    label, _, pred = lexer.expect_type(SYMBOL, COLON, SYMBOL)
    lnk = _decode_lnk(lexer)
    arglist, carg = _decode_arglist(lexer, variables)
    argtypes = [variable.type(arg) for arg in arglist]
    synopsis = semi.find_synopsis(pred, argtypes)
    args = {d[0]: v for d, v in zip(synopsis, arglist)}
    if carg:
        args[CONSTANT_ROLE] = carg
    return EP(
        pred,
        label,
        args=args,
        lnk=lnk,
        surface=None,
        base=None)


def _decode_lnk(lexer):
    lnk = lexer.accept_type(LNK)
    if lnk is not None:
        lnk = Lnk(lnk)
    return lnk


def _decode_arglist(lexer, variables):
    arglist = []
    carg = None
    lexer.expect_type(LPAREN)
    if lexer.peek()[0] != RPAREN:
        while True:
            gid, arg = lexer.choice_type(SYMBOL, DQSTRING)
            if gid == SYMBOL:
                if lexer.accept_type(COLON):
                    variables[arg] = _decode_proplist(lexer)
                arglist.append(arg)
            else:
                carg = arg
            if not lexer.accept_type(COMMA):
                break
    lexer.expect_type(RPAREN)
    return arglist, carg


def _decode_cons(lexer, cls):
    cons = []
    lexer.expect_type(LBRACE)
    if lexer.peek()[0] != RBRACE:
        while True:
            lhs, reln, rhs = lexer.expect_type(SYMBOL, SYMBOL, SYMBOL)
            cons.append(cls(lhs, reln, rhs))
            if not lexer.accept_type(COMMA):
                break
    lexer.expect_type(RBRACE)
    return cons


def _match_properties(variables, semi):
    for var, propvals in variables.items():
        if not propvals:
            continue
        semiprops = semi.variables[variable.type(var)]
        assert len(semiprops) == len(propvals)
        assert all(semi.properties.subsumes(sp[1], pv)
                   for sp, pv in zip(semiprops, propvals))
        variables[var] = {sp[0]: pv for sp, pv in zip(semiprops, propvals)}


##############################################################################
##############################################################################
# Encoding


def _encode(ms, semi, properties, lnk, indent):
    if indent is None or indent is False:
        delim = ' '
    else:
        delim = '\n'
    return delim.join(
        _encode_indexed(m, semi, properties, lnk, indent)
        for m in ms)


def _encode_indexed(m, semi, properties, lnk, indent):
    # attempt to convert if necessary
    # if not isinstance(m, MRS):
    #     m = MRS.from_xmrs(m)

    if indent is None or indent is False:
        i1 = ',{{{}}}'
        i2 = i3 = ','
        start = '<'
        end = '>'
        hook = '{},{}'
    else:
        if indent is True:
            indent = 2
        i1 = ',\n' + (' ' * indent) + '{{' + (' ' * (indent - 1)) + '{} }}'
        i2 = ',\n' + ('  ' * indent)
        i3 = ', '
        start = '< '
        end = ' >'
        hook = '{}, {}'

    if properties:
        varprops = _prepare_variable_properties(m, semi)
    else:
        varprops = {}

    body = [
        hook.format(m.top, _encode_variable(m.index, varprops)),
        i1.format(i2.join(_encode_rel(ep, semi, varprops, lnk, i3)
                          for ep in m.rels)),
        i1.format(i2.join(_encode_hcons(hc)
                          for hc in m.hcons))
    ]
    if m.icons:
        body.append(
            i1.format(i2.join(_encode_icons(ic)
                              for ic in m.icons)))

    return start + ''.join(body) + end


def _prepare_variable_properties(m, semi):
    proplists = {}
    for var, varprops in m.variables.items():
        if varprops:
            proplists[var] = [
                varprops.get(key, val).upper()
                for key, val in semi.variables[variable.type(var)]]
    return proplists


def _encode_variable(var, varprops):
    if var in varprops:
        props = ':' + ':'.join(varprops[var])
        del varprops[var]
    else:
        props = ''
    return var + props


def _encode_rel(ep, semi, varprops, lnk, delim):
    roles = {role: None for role in ep.args if role != CONSTANT_ROLE}
    synopsis = semi.find_synopsis(ep.predicate, roles)
    args = [_encode_variable(ep.args[d.name], varprops)
            for d in synopsis
            if d.name in ep.args]
    if ep.carg is not None:
        args.append('"{}"'.format(ep.carg))
    return '{label}:{pred}{lnk}({args})'.format(
        label=ep.label,
        pred=ep.predicate,
        lnk=str(ep.lnk) if lnk else '',
        args=delim.join(args))


def _encode_hcons(hc):
    return '{} {} {}'.format(hc.hi, hc.relation, hc.lo)


def _encode_icons(ic):
    return '{} {} {}'.format(ic.left, ic.relation, ic.right)
