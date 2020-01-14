# -*- coding: utf-8 -*-

"""
DMRS-PENMAN serialization and deserialization.
"""

from pathlib import Path
import logging

import penman

from delphin.exceptions import PyDelphinException
from delphin.lnk import Lnk
from delphin.dmrs import DMRS, Node, Link, CVARSORT
from delphin.dmrs._dmrs import FIRST_NODE_ID
from delphin.sembase import property_priority
from delphin.util import _bfs


logger = logging.getLogger(__name__)


CODEC_INFO = {
    'representation': 'dmrs',
}


def load(source):
    """
    Deserialize PENMAN graphs from a file (handle or filename)

    Args:
        source: filename or file object
    Returns:
        a list of DMRS objects
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
    Deserialize PENMAN graphs from a string

    Args:
        s (str): serialized PENMAN graphs
    Returns:
        a list of DMRS objects
    """
    try:
        graphs = penman.loads(s)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc
    xs = [from_triples(g.triples) for g in graphs]
    return xs


def dump(ds, destination, properties=False, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize DMRS objects to a PENMAN file.

    Args:
        destination: filename or file object
        ds: iterator of :class:`~delphin.mrs.dmrs.DMRS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ds, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ds, properties=False, lnk=True, indent=False):
    """
    Serialize DMRS objects to a PENMAN string.

    Args:
        ds: iterator of :class:`~delphin.mrs.dmrs.DMRS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        a PENMAN-serialization of the DMRS objects
    """
    if indent is True:
        indent = -1
    elif indent is False:
        indent = None
    to_graph = penman.Graph
    graphs = [to_graph(to_triples(d, properties=properties, lnk=lnk))
              for d in ds]
    try:
        return penman.dumps(graphs, indent=indent)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc


def decode(s):
    """
    Deserialize a DMRS object from a PENMAN string.
    """
    try:
        g = penman.decode(s)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc

    return from_triples(g.triples)


def encode(d, properties=True, lnk=True, indent=False):
    """
    Serialize a DMRS object to a PENMAN string.

    Args:
        d: a DMRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a PENMAN-serialization of the DMRS object
    """
    if indent is True:
        indent = -1
    elif indent is False:
        indent = None
    triples = to_triples(d, properties=properties, lnk=lnk)
    g = penman.Graph(triples)
    try:
        return penman.encode(g, indent=indent)
    except penman.PenmanError as exc:
        raise PyDelphinException('could not decode with Penman') from exc


def to_triples(d, properties=True, lnk=True):
    """
    Encode *d* as triples suitable for PENMAN serialization.
    """
    # determine if graph is connected
    g = {node.id: set() for node in d.nodes}
    for link in d.links:
        g[link.start].add(link.end)
        g[link.end].add(link.start)
    main_component = _bfs(g, start=d.top)
    complete = True

    idmap = {}
    quantifiers = {node.id for node in d.nodes
                   if d.is_quantifier(node.id)}
    for i, node in enumerate(d.nodes, 1):
        if node.id in quantifiers:
            idmap[node.id] = 'q' + str(i)
        else:
            idmap[node.id] = '{}{}'.format(node.type or '_', i)
    # sort the nodes so the top node appears first
    nodes = sorted(d.nodes, key=lambda n: d.top != n.id)
    triples = []
    for node in nodes:
        if node.id in main_component:
            _id = idmap[node.id]
            triples.append((_id, ':instance', node.predicate))
            if lnk and node.lnk is not None:
                triples.append((_id, ':lnk', '"{}"'.format(str(node.lnk))))
            if node.carg is not None:
                triples.append((_id, ':carg', '"{}"'.format(node.carg)))
            if node.type:
                triples.append((_id, ':' + CVARSORT, node.type))
            if properties:
                for key in sorted(node.properties, key=property_priority):
                    value = node.properties[key]
                    triples.append((_id, ':' + key.lower(), value))
        else:
            complete = False

    # if d.top is not None:
    #     triples.append((None, 'top', d.top))
    for link in d.links:
        if link.start in main_component and link.end in main_component:
            start = idmap[link.start]
            end = idmap[link.end]
            relation = ':{}-{}'.format(link.role.upper(), link.post)
            triples.append((start, relation, end))

    if not complete:
        logger.warning(
            'disconnected graph cannot be completely encoded: %r', d)
    return triples


def from_triples(triples):
    """
    Decode triples, as from :func:`to_triples`, into a DMRS object.
    """
    top = lnk = surface = identifier = None
    nids, nd, edges = [], {}, []
    for src, rel, tgt in triples:
        rel = rel.lstrip(':')
        src, tgt = str(src), str(tgt)  # in case penman converts ids to ints
        if src is None and rel == 'top':
            top = tgt
            continue
        elif src not in nd:
            if top is None:
                top = src
            nids.append(src)
            nd[src] = {'pred': None, 'lnk': None, 'type': None,
                       'props': {}, 'carg': None}
        if rel == 'instance':
            nd[src]['pred'] = tgt
        elif rel == 'lnk':
            cfrom, cto = tgt.strip('"<>').split(':')
            nd[src]['lnk'] = Lnk.charspan(int(cfrom), int(cto))
        elif rel == 'carg':
            if (tgt[0], tgt[-1]) == ('"', '"'):
                tgt = tgt[1:-1]
            nd[src]['carg'] = tgt
        elif rel == CVARSORT:
            nd[src]['type'] = tgt
        elif rel.islower():
            nd[src]['props'][rel] = tgt
        else:
            rargname, post = rel.rsplit('-', 1)
            edges.append((src, tgt, rargname, post))
    nidmap = dict((nid, FIRST_NODE_ID + i) for i, nid in enumerate(nids))
    nodes = [
        Node(id=nidmap[nid],
             predicate=nd[nid]['pred'],
             type=nd[nid]['type'],
             properties=nd[nid]['props'],
             lnk=nd[nid]['lnk'],
             carg=nd[nid]['carg'])
        for i, nid in enumerate(nids)
    ]
    links = [Link(nidmap[s], nidmap[t], r, p) for s, t, r, p in edges]
    return DMRS(
        top=nidmap[top],
        nodes=nodes,
        links=links,
        lnk=lnk,
        surface=surface,
        identifier=identifier
    )
