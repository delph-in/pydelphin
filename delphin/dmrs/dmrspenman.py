
"""
DMRS-PENMAN serialization and deserialization.
"""

import penman

from delphin.lnk import Lnk
from delphin.dmrs import DMRS, Node, Link, CVARSORT
from delphin.dmrs._dmrs import FIRST_NODE_ID
from delphin.sembase import property_priority


def load(source):
    """
    Deserialize PENMAN graphs from a file (handle or filename)

    Args:
        source: filename or file object
    Returns:
        a list of DMRS objects
    """
    graphs = penman.load(fh)
    xs = [from_triples(g.triples()) for g in graphs]
    return xs


def loads(s):
    """
    Deserialize PENMAN graphs from a string

    Args:
        s (str): serialized PENMAN graphs
    Returns:
        a list of DMRS objects
    """
    graphs = penman.loads(s)
    xs = [from_triples(g.triples()) for g in graphs]
    return xs


def dump(ds, destination, properties=False, indent=True, encoding='utf-8'):
    """
    Serialize DMRS objects to a PENMAN file.

    Args:
        destination: filename or file object
        ds: iterator of :class:`~delphin.mrs.dmrs.DMRS` objects to
            serialize
        properties: if `True`, encode variable properties
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ds, properties=properties, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ds, properties=False, indent=True):
    """
    Serialize DMRS objects to a PENMAN string.

    Args:
        ds: iterator of :class:`~delphin.mrs.dmrs.DMRS` objects to
            serialize
        properties: if `True`, encode variable properties
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        a PENMAN-serialization of the DMRS objects
    """
    codec = penman.PENMANCodec()
    to_graph = codec.triples_to_graph
    graphs = [to_graph(to_triples(d, properties=properties)) for d in ds]
    return penman.dumps(graphs, indent=indent)


def decode(s):
    """
    Deserialize a DMRS object from a PENMAN string.
    """
    return from_triples(penman.decode(s).triples())


def encode(d, properties=True, indent=False):
    """
    Serialize a DMRS object to a PENMAN string.

    Args:
        d: a DMRS object
        properties (bool): if `False`, suppress variable properties
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a PENMAN-serialization of the DMRS object
    """
    triples = to_triples(d, properties=properties)
    g = penman.PENMANCodec().triples_to_graph(triples)
    return penman.encode(g, indent=indent)


def to_triples(dmrs, properties=True):
    """
    Encode *dmrs* as triples suitable for PENMAN serialization.
    """
    # attempt to convert if necessary
    # if not isinstance(dmrs, DMRS):
    #     dmrs = DMRS.from_xmrs(dmrs)

    idmap = {}
    quantifiers = {node.id for node in dmrs.nodes
                   if dmrs.is_quantifier(node.id)}
    for i, node in enumerate(dmrs.nodes, 1):
        if node.id in quantifiers:
            idmap[node.id] = 'q' + str(i)
        else:
            idmap[node.id] = '{}{}'.format(node.type or '_', i)
    # sort the nodes so the top node appears first
    nodes = sorted(dmrs.nodes, key=lambda n: dmrs.top != n.id)
    triples = []
    for node in nodes:
        _id = idmap[node.id]
        triples.append((_id, 'instance', node.predicate))
        if node.lnk is not None:
            triples.append((_id, 'lnk', '"{}"'.format(str(node.lnk))))
        if node.carg is not None:
            triples.append((_id, 'carg', '"{}"'.format(node.carg)))
        if node.type:
            triples.append((_id, CVARSORT, node.type))
        if properties:
            for key in sorted(node.properties, key=property_priority):
                value = node.properties[key]
                triples.append((_id, key.lower(), value))

    # if dmrs.top is not None:
    #     triples.append((None, 'top', dmrs.top))
    for link in dmrs.links:
        start = idmap[link.start]
        end = idmap[link.end]
        relation = '{}-{}'.format(link.role.upper(), link.post)
        triples.append((start, relation, end))
    return triples


def from_triples(triples):
    """
    Decode triples into a DMRS object.
    """
    top = lnk = surface = identifier = None
    nids, nd, edges = [], {}, []
    for src, rel, tgt in triples:
        src, tgt = str(src), str(tgt)  # in case penman converts ids to ints
        if src is None and rel == 'top':
            top = tgt
            continue
        elif src not in nd:
            if top is None:
                top=src
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

