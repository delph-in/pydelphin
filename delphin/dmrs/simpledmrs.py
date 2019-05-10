# -*- coding: utf-8 -*-

"""
Serialization for the SimpleDMRS format.

Example:

* *The new chef whose soup accidentally spilled quit and left.*

::

  dmrs {
    [("The new chef whose soup accidentally spilled quit and left.") top=10008 index=10009]
    10000 [_the_q<0:3> x];
    10001 [_new_a_1<4:7> e PROG=bool MOOD=indicative TENSE=untensed PERF=- SF=prop];
    10002 [_chef_n_1<8:12> x PERS=3 IND=+ NUM=sg];
    10003 [def_explicit_q<13:18> x];
    10004 [poss<13:18> e PROG=- MOOD=indicative TENSE=untensed PERF=- SF=prop];
    10005 [_soup_n_1<19:23> x PERS=3 NUM=sg];
    10006 [_accidental_a_1<24:36> e PROG=- MOOD=indicative TENSE=untensed PERF=- SF=prop];
    10007 [_spill_v_1<37:44> e PROG=- MOOD=indicative TENSE=past PERF=- SF=prop];
    10008 [_quit_v_1<45:49> e PROG=- MOOD=indicative TENSE=past PERF=- SF=prop];
    10009 [_and_c<50:53> e PROG=- MOOD=indicative TENSE=past PERF=- SF=prop];
    10010 [_leave_v_1<54:59> e PROG=- MOOD=indicative TENSE=past PERF=- SF=prop];
    10004:ARG2/NEQ -> 10002;
    10004:ARG1/EQ -> 10005;
    10000:RSTR/H -> 10002;
    10003:RSTR/H -> 10005;
    10010:ARG1/NEQ -> 10002;
    10007:ARG1/NEQ -> 10005;
    10008:ARG1/NEQ -> 10002;
    10006:ARG1/EQ -> 10007;
    10001:ARG1/EQ -> 10002;
    10009:ARG2/EQ -> 10010;
    10009:ARG1/EQ -> 10008;
    10010:MOD/EQ -> 10008;
    10007:MOD/EQ -> 10002;
  }

"""

from delphin.lnk import Lnk

from delphin.dmrs import (
    DMRS,
    Node,
    Link,
    EQ_POST,
    DMRSSyntaxError,
)
from delphin.util import Lexer


##############################################################################
##############################################################################
# Pickle-API methods

def load(source):
    """
    Deserialize SimpleDMRS from a file (handle or filename)

    Args:
        source (str, file): input filename or file object
    Returns:
        a list of DMRS objects
    """
    if hasattr(source, 'read'):
        ds = list(_decode(source))
    else:
        with open(source) as fh:
            ds = list(_decode(fh))
    return ds


def loads(s, encoding='utf-8'):
    """
    Deserialize SimpleDMRS string representations

    Args:
        s (str): a SimpleDMRS string
    Returns:
        a list of DMRS objects
    """
    ds = list(_decode(s.splitlines()))
    return ds


def dump(ds, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize DMRS objects to SimpleDMRS and write to a file

    Args:
        ds: an iterator of DMRS objects to serialize
        destination: filename or file object where data will be written
        properties: if `False`, suppress morphosemantic properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ds, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ds, properties=True, lnk=True, indent=False):
    """
    Serialize DMRS objects to a SimpleDMRS representation

    Args:
        ds: an iterator of DMRS objects to serialize
        properties: if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a SimpleDMRS string representation of a corpus of DMRS objects
    """
    return _encode(ds, properties, lnk, indent)


def decode(s):
    """
    Deserialize a DMRS object from a SimpleDMRS string.
    """
    lexer = _SimpleDMRSLexer.lex(s.splitlines())
    return _decode_dmrs(lexer)


def encode(d, properties=True, lnk=True, indent=False):
    """
    Serialize a DMRS object to a SimpleDMRS string.

    Args:
        d: a DMRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a SimpleDMRS-serialization of the DMRS object
    """
    return _encode([d], properties, lnk, indent)


##############################################################################
##############################################################################
# Decoding

_SimpleDMRSLexer = Lexer(
    tokens=[
        (r'\{', 'LBRACE:{'),
        (r'\}', 'RBRACE:}'),
        (r'\[', 'LBRACKET:['),
        (r'\]', 'RBRACKET:]'),
        (r'<(?:-?\d+[:#]-?\d+|@\d+|\d+(?: +\d+)*)>', 'LNK:a lnk value'),
        (r'\("([^"\\]*(?:\\.[^"\\]*)*)"\)', 'DQSTRING:a string'),
        (r':', 'COLON::'),
        (r'\/', 'SLASH:/'),
        (r'=', 'EQUALS:='),
        (r';', 'SEMICOLON:;'),
        (r'(--|->)', 'ARROW:a link arrow'),
        (r'[^\s"\'()\/:;<=>[\]{}]+', 'SYMBOL:a symbol'),
        (r'[^\s]',  'UNEXPECTED')
    ],
    error_class=DMRSSyntaxError)

LBRACE    = _SimpleDMRSLexer.tokentypes.LBRACE
RBRACE    = _SimpleDMRSLexer.tokentypes.RBRACE
LBRACKET  = _SimpleDMRSLexer.tokentypes.LBRACKET
RBRACKET  = _SimpleDMRSLexer.tokentypes.RBRACKET
LNK       = _SimpleDMRSLexer.tokentypes.LNK
DQSTRING  = _SimpleDMRSLexer.tokentypes.DQSTRING
COLON     = _SimpleDMRSLexer.tokentypes.COLON
SLASH     = _SimpleDMRSLexer.tokentypes.SLASH
EQUALS    = _SimpleDMRSLexer.tokentypes.EQUALS
SEMICOLON = _SimpleDMRSLexer.tokentypes.SEMICOLON
ARROW     = _SimpleDMRSLexer.tokentypes.ARROW
SYMBOL    = _SimpleDMRSLexer.tokentypes.SYMBOL


def _decode(lineiter):
    lexer = _SimpleDMRSLexer.lex(lineiter)
    try:
        while lexer.peek():
            yield _decode_dmrs(lexer)
    except StopIteration:
        pass


def _decode_dmrs(lexer):
    top = index = lnk = surface = identifier = None
    lexer.expect_form('dmrs')
    identifier = lexer.accept_type(SYMBOL)
    lexer.expect_type(LBRACE)
    if lexer.accept_type(LBRACKET):
        lnk = _decode_lnk(lexer)
        surface = lexer.accept_type(DQSTRING)
        graphprops = dict(_decode_properties(lexer))
        top = graphprops.get('TOP')
        index = graphprops.get('INDEX')

    nodes = []
    links = []
    while lexer.peek()[0] != RBRACE:
        nodeid = lexer.expect_type(SYMBOL)
        gid, _ = lexer.choice_type(LBRACKET, COLON)
        if gid == LBRACKET:
            nodes.append(_decode_node(nodeid, lexer))
        else:
            links.append(_decode_link(nodeid, lexer))
    lexer.expect_type(RBRACE)

    return DMRS(top=int(top),
                index=int(index),
                nodes=nodes,
                links=links,
                lnk=lnk,
                surface=surface,
                identifier=identifier)


def _decode_lnk(lexer):
    lnk = lexer.accept_type(LNK)
    if lnk is not None:
        lnk = Lnk(lnk)
    return lnk


def _decode_properties(lexer):
    props = []
    while lexer.peek()[0] != RBRACKET:
        prop, _, val = lexer.expect_type(SYMBOL, EQUALS, SYMBOL)
        props.append((prop.upper(), val.lower()))
    lexer.expect_type(RBRACKET)
    return props


def _decode_node(nodeid, lexer):
    predicate = lexer.expect_type(SYMBOL)
    lnk = _decode_lnk(lexer)
    carg = lexer.accept_type(DQSTRING)
    nodetype = lexer.accept_type(SYMBOL)
    properties = dict(_decode_properties(lexer))
    lexer.expect_type(SEMICOLON)
    return Node(int(nodeid), predicate, type=nodetype,
                properties=properties, carg=carg, lnk=lnk)


def _decode_link(start, lexer):
    role = lexer.accept_type(SYMBOL)
    _, post, _, end, _ = lexer.expect_type(
        SLASH, SYMBOL, ARROW, SYMBOL, SEMICOLON)
    return Link(int(start), int(end), role, post)


##############################################################################
##############################################################################
# Encoding


_node = '{nodeid} [{pred}{lnk}{carg}{sortinfo}];'
_link = '{start}:{pre}/{post} {arrow} {end};'


def _encode(ds, properties, lnk, indent):
    if indent is None or indent is False:
        indent = None  # normalize False to None
        delim = ' '
    else:
        if indent is True:
            indent = 2
        delim = '\n'
    return delim.join(_encode_dmrs(d, properties, lnk, indent)
                      for d in ds)


def _encode_dmrs(d, properties, lnk, indent):
    # attempt to convert if necessary
    # if not isinstance(d, DMRS):
    #     d = DMRS.from_xmrs(d)

    if indent is None:
        delim = ' '
        end = ' }'
    else:
        delim = '\n' + ' ' * indent
        end = '\n}'
    if d.identifier is None:
        start = 'dmrs {'
    else:
        start = 'dmrs {} {{'.format(d.identifier)
    attrs = _encode_attrs(d, lnk)
    nodes = [_encode_node(node, properties, lnk) for node in d.nodes]
    links = [_encode_link(link) for link in d.links]
    return delim.join([start] + attrs + nodes + links) + end


def _encode_attrs(d, lnk):
    attrs = []
    if lnk:
        if d.lnk:
            attrs.append(str(d.lnk))
        if d.surface is not None:
            # join without space to lnk, if any
            attrs = [''.join(attrs + ['("{}")'.format(d.surface)])]
    if d.top is not None:
        attrs.append('top={}'.format(d.top))
    if d.index is not None:
        attrs.append('index={}'.format(d.index))
    if attrs:
        attrs = ['[{}]'.format(' '.join(attrs))]
    return attrs


def _encode_node(node, properties, lnk):
    return _node.format(
        nodeid=node.id,
        pred=node.predicate,
        lnk=str(node.lnk) if lnk else '',
        carg='' if node.carg is None else '("{}")'.format(node.carg),
        sortinfo=_encode_sortinfo(node, properties))


def _encode_sortinfo(node, properties):
    sortinfo = []
    # rather than node.sortinfo, construct manually so cvarsort appears first
    if node.type is not None and node.type != 'u':
        sortinfo.append(node.type)
    if properties and node.properties:
        sortinfo.extend('{}={}'.format(k, v)
                        for k, v in node.properties.items())
    if sortinfo:
        return ' ' + ' '.join(sortinfo)
    return ''


def _encode_link(link):
    return _link.format(
        start=link.start,
        pre=link.role or '',
        post=link.post,
        arrow='->' if link.role or link.post != EQ_POST else '--',
        end=link.end)
