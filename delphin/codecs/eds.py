# -*- coding: utf-8 -*-

"""
Serialization functions for the "native" EDS format.
"""

from pathlib import Path

from delphin import variable
from delphin.lnk import Lnk
from delphin.sembase import (role_priority, property_priority)
from delphin.eds import (EDS, Node, EDSSyntaxError)
from delphin.util import (_bfs, Lexer)


CODEC_INFO = {
    'representation': 'eds',
}


def load(source):
    """
    Deserialize an EDS file (handle or filename) to EDS objects

    Args:
        source: filename or file object
    Returns:
        a list of EDS objects
    """
    if hasattr(source, 'read'):
        data = list(_decode(source))
    else:
        source = Path(source).expanduser()
        with source.open() as fh:
            data = list(_decode(fh))
    return data


def loads(s):
    """
    Deserialize an EDS string to EDS objects

    Args:
        s (str): an EDS string
    Returns:
        a list of EDS objects
    """
    data = list(_decode(s.splitlines()))
    return data


def dump(es, destination, properties=True, lnk=True, show_status=False,
         indent=False, encoding='utf-8'):
    """
    Serialize EDS objects to an EDS file.

    Args:
        destination: filename or file object
        es: iterator of :class:`~delphin.eds.EDS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        show_status (bool): if `True`, indicate disconnected components
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    string = dumps(es, properties=properties, lnk=lnk,
                   show_status=show_status, indent=indent)
    if hasattr(destination, 'write'):
        print(string, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(string, file=fh)


def dumps(es, properties=True, lnk=True, show_status=False, indent=False):
    """
    Serialize EDS objects to an EDS string.

    Args:
        es: iterator of :class:`~delphin.eds.EDS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        show_status (bool): if `True`, indicate disconnected components
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        an EDS-serialization of the EDS objects
    """
    if indent is None or indent is False:
        delim = ' '
    else:
        delim = '\n'
    return delim.join(
        encode(e, properties=properties, lnk=lnk,
               show_status=show_status, indent=indent)
        for e in es)


def decode(s):
    """
    Deserialize an EDS object from an EDS string.
    """
    lexer = _EDSLexer.lex(s.splitlines())
    return _decode_eds(lexer)


def encode(e, properties=True, lnk=True, show_status=False, indent=False):
    """
    Serialize an EDS object to an EDS string.

    Args:
        e: an EDS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        show_status (bool): if `True`, indicate disconnected components
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        an EDS-serialization of the EDS object
    """
    if indent is None or indent is False:
        indent = False
    else:
        indent = True
    return _encode_eds(e, properties, lnk, show_status, indent)


##############################################################################
##############################################################################
# Decoding

_EDSLexer = Lexer(
    tokens=[
        (r'\{', 'LBRACE:{'),
        (r'\}', 'RBRACE:}'),
        (r'\((?:cyclic *)?(?:fragmented)?\)', 'GRAPHSTATUS'),
        (r'\|', 'NODESTATUS:|'),
        (r'<(?:-?\d+[:#]-?\d+|@\d+|\d+(?: +\d+)*)>', 'LNK:a lnk value'),
        (r'\("([^"\\]*(?:\\.[^"\\]*)*)"\)', 'CARG:a string'),
        (r':', 'COLON::'),
        (r',', 'COMMA:,'),
        (r'\[', 'LBRACKET:['),
        (r'\]', 'RBRACKET:]'),
        (r'[^ \n:,<\(\[\]\{\}]+', 'SYMBOL:a symbol'),
        (r'[^\s]', 'UNEXPECTED')
    ],
    error_class=EDSSyntaxError)

LBRACE      = _EDSLexer.tokentypes.LBRACE
RBRACE      = _EDSLexer.tokentypes.RBRACE
GRAPHSTATUS = _EDSLexer.tokentypes.GRAPHSTATUS
NODESTATUS  = _EDSLexer.tokentypes.NODESTATUS
LNK         = _EDSLexer.tokentypes.LNK
CARG        = _EDSLexer.tokentypes.CARG
COLON       = _EDSLexer.tokentypes.COLON
COMMA       = _EDSLexer.tokentypes.COMMA
LBRACKET    = _EDSLexer.tokentypes.LBRACKET
RBRACKET    = _EDSLexer.tokentypes.RBRACKET
SYMBOL      = _EDSLexer.tokentypes.SYMBOL


def _decode(lineiter):
    lexer = _EDSLexer.lex(lineiter)
    try:
        while lexer.peek():
            yield _decode_eds(lexer)
    except StopIteration:
        pass


def _decode_eds(lexer):
    _, top, _ = lexer.expect_type(LBRACE, SYMBOL, COLON)
    lexer.accept_type(GRAPHSTATUS)
    nodes = []
    while lexer.peek()[0] != RBRACE:
        lexer.accept_type(NODESTATUS)
        start, _ = lexer.expect_type(SYMBOL, COLON)
        nodes.append(_decode_node(start, lexer))
    lexer.expect_type(RBRACE)
    return EDS(top=top, nodes=nodes)


def _decode_node(start, lexer):
    predicate = lexer.expect_type(SYMBOL).lower()
    lnk = Lnk(lexer.accept_type(LNK))
    carg = lexer.accept_type(CARG)
    nodetype, properties = _decode_properties(start, lexer)
    edges = _decode_edges(start, lexer)
    return Node(start, predicate, nodetype, edges, properties, carg, lnk)


def _decode_properties(start, lexer):
    nodetype = None
    properties = {}
    if lexer.accept_type(LBRACE):
        nodetype = lexer.expect_type(SYMBOL)
        if lexer.peek()[0] != RBRACE:
            while True:
                prop, val = lexer.expect_type(SYMBOL, SYMBOL)
                properties[prop.upper()] = val.lower()
                if not lexer.accept_type(COMMA):
                    break
        lexer.expect_type(RBRACE)
    return nodetype, properties


def _decode_edges(start, lexer):
    edges = {}
    lexer.expect_type(LBRACKET)
    if lexer.peek()[0] != RBRACKET:
        while True:
            role, end = lexer.expect_type(SYMBOL, SYMBOL)
            edges[role.upper()] = end
            if not lexer.accept_type(COMMA):
                break
    lexer.expect_type(RBRACKET)
    return edges


##############################################################################
##############################################################################
# Encoding

def _encode_eds(e, properties, lnk, show_status, indent):
    # do something predictable for empty EDS
    if len(e.nodes) == 0:
        return '{:\n}' if indent else '{:}'

    # determine if graph is connected
    g = {node.id: set() for node in e.nodes}
    for node in e.nodes:
        for target in node.edges.values():
            g[node.id].add(target)
            g[target].add(node.id)
    nidgrp = _bfs(g, start=e.top)

    status = ''
    if show_status and nidgrp != set(g):
        status = ' (fragmented)'
    delim = '\n' if indent else ' '
    connected = ' ' if indent else ''
    disconnected = '|' if show_status else ' '

    ed_list = []
    for node in e.nodes:
        membership = connected if node.id in nidgrp else disconnected
        ed_list.append(membership + _encode_node(node, properties, lnk))

    return '{{{top}{status}{delim}{ed_list}{enddelim}}}'.format(
        top=e.top + ':' if e.top is not None else ':',
        status=status,
        delim=delim,
        ed_list=delim.join(ed_list),
        enddelim='\n' if indent else ''
    )


def _encode_node(node, properties, lnk):
    parts = [node.id, ':', node.predicate]

    if lnk and node.lnk:
        parts.append(str(node.lnk))

    if node.carg is not None:
        parts.append('("{}")'.format(node.carg))

    if properties and (node.properties or node.type):
        parts.append('{')
        parts.append(node.type or variable.UNSPECIFIC)
        if node.properties:
            proplist = ['{} {}'.format(prop, node.properties[prop])
                        for prop in sorted(node.properties,
                                           key=property_priority)]
            parts.append(' ' + ', '.join(proplist))
        parts.append('}')

    parts.append('[')
    edgelist = []
    edges = node.edges
    for role in sorted(edges, key=role_priority):
        edgelist.append('{} {}'.format(role, edges[role]))
    parts.append(', '.join(edgelist))
    parts.append(']')

    return ''.join(parts)
