
"""
Serialization for the Indexed MRS format.
"""

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
