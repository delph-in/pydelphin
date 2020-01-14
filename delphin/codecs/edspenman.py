# -*- coding: utf-8 -*-

"""
EDS-PENMAN serialization and deserialization.
"""

from pathlib import Path
import logging

import penman

from delphin.exceptions import PyDelphinException
from delphin.lnk import Lnk
from delphin.sembase import (role_priority, property_priority)
from delphin.eds import (EDS, Node)
from delphin.util import _bfs


logger = logging.getLogger(__name__)


CODEC_INFO = {
    'representation': 'eds',
}


def load(source):
    """
    Deserialize a EDS-PENMAN file (handle or filename) to EDS objects.

    Args:
        source: filename or file object
    Returns:
        a list of EDS objects
    """
    if not hasattr(source, 'read'):
        source = Path(source).expanduser()
    try:
        graphs = penman.load(source)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc
    xs = [from_triples(g.triples) for g in graphs]
    return xs


def loads(s):
    """
    Deserialize a EDS-PENMAN string to EDS objects.

    Args:
        s (str): a EDS-PENMAN string
    Returns:
        a list of EDS objects
    """
    try:
        graphs = penman.loads(s)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc
    xs = [from_triples(g.triples) for g in graphs]
    return xs


def dump(es, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize EDS objects to a EDS-PENMAN file.

    Args:
        destination: filename or file object
        es: iterator of :class:`~delphin.eds.EDS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(es, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(es, properties=True, lnk=True, indent=False):
    """
    Serialize EDS objects to a EDS-PENMAN string.

    Args:
        es: iterator of :class:`~delphin.eds.EDS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        a EDS-PENMAN-serialization of the EDS objects
    """
    if indent is True:
        indent = -1
    elif indent is False:
        indent = None
    to_graph = penman.Graph
    graphs = [to_graph(to_triples(e, properties=properties, lnk=lnk))
              for e in es]
    try:
        return penman.dumps(graphs, indent=indent)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not encode with Penman') from exc


def decode(s):
    """
    Deserialize a EDS object from a EDS-PENMAN string.
    """
    try:
        g = penman.decode(s)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc

    return from_triples(g.triples)


def encode(e, properties=True, lnk=True, indent=False):
    """
    Serialize the EDS object *e* to an EDS-PENMAN string.

    Args:
        e: a EDS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a EDS-PENMAN-serialization of the EDS object
    """
    if indent is True:
        indent = -1
    elif indent is False:
        indent = None
    triples = to_triples(e, properties=properties, lnk=lnk)
    g = penman.Graph(triples)
    try:
        return penman.encode(g, indent=indent)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not encode with Penman') from exc


def to_triples(e, properties=True, lnk=True):
    """
    Encode the Eds as triples suitable for PENMAN serialization.
    """
    # determine if graph is connected
    g = {node.id: set() for node in e.nodes}
    for node in e.nodes:
        for target in node.edges.values():
            g[node.id].add(target)
            g[target].add(node.id)
    main_component = _bfs(g, start=e.top)
    complete = True

    triples = []
    # sort node ids just so top var is first
    nodes = sorted(e.nodes, key=lambda n: n.id != e.top)
    for node in nodes:
        nid = node.id
        if nid in main_component:
            triples.append((nid, ':instance', node.predicate))
            if lnk and node.lnk:
                triples.append((nid, ':lnk', '"{}"'.format(str(node.lnk))))
            if node.carg:
                triples.append((nid, ':carg', '"{}"'.format(node.carg)))
            if node.type is not None:
                triples.append((nid, ':type', node.type))
            if properties:
                for prop in sorted(node.properties, key=property_priority):
                    rel = ':' + prop.lower()
                    triples.append((nid, rel, node.properties[prop]))
            for role in sorted(node.edges, key=role_priority):
                triples.append((nid, ':' + role, node.edges[role]))
        else:
            complete = False

    if not complete:
        logger.warning(
            'disconnected graph cannot be completely encoded: %r', e)
    return triples


def from_triples(triples):
    """
    Decode triples, as from :func:`to_triples`, into an EDS object.
    """
    nids, nd = [], {}
    for src, rel, tgt in triples:
        rel = rel.lstrip(':')
        if src not in nd:
            nids.append(src)
            nd[src] = {'pred': None, 'type': None, 'edges': {},
                       'props': {}, 'lnk': None, 'carg': None}
        if rel == 'instance':
            nd[src]['pred'] = tgt
        elif rel == 'lnk':
            nd[src]['lnk'] = Lnk(tgt.strip('"'))
        elif rel == 'carg':
            if (tgt[0], tgt[-1]) == ('"', '"'):
                tgt = tgt[1:-1]
            nd[src]['carg'] = tgt
        elif rel == 'type':
            nd[src]['type'] = tgt
        elif rel.islower():
            nd[src]['props'][rel.upper()] = tgt
        else:
            nd[src]['edges'][rel] = tgt
    nodes = [Node(nid,
                  nd[nid]['pred'],
                  type=nd[nid]['type'],
                  edges=nd[nid]['edges'],
                  properties=nd[nid]['props'],
                  carg=nd[nid]['carg'],
                  lnk=nd[nid]['lnk'])
             for nid in nids]
    top = nids[0] if nids else None
    return EDS(top=top, nodes=nodes)
