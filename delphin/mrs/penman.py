
"""
Serialization functions for the PENMAN graph format.

Unlike other *MRS serializers, this one takes a *model* argument for
the load(), loads(), dump(), and dumps() methods, which determines what
the graph will look like. This is because DMRS and EDS (and possibly
others) yield different graph structures, but both can be encoded as
PENMAN graphs. In this sense, it's more like JSON formatting of *MRS.
"""

from __future__ import absolute_import, print_function

import penman

from delphin.mrs.config import LTOP_NODEID


class XMRSCodec(penman.PENMANCodec):
    TYPE_REL = 'predicate'
    TOP_VAR = LTOP_NODEID
    TOP_REL = 'top'


def load(fh, model):
    """
    Deserialize PENMAN graphs from a file (handle or filename)

    Args:
        fh: filename or file object
        model: the Xmrs subclass instantiated from decoded triples
    Returns:
        a list of objects (of class *model*)
    """
    graphs = penman.load(fh, cls=XMRSCodec)
    xs = [model.from_triples(g.triples()) for g in graphs]
    return xs


def loads(s, model):
    """
    Deserialize PENMAN graphs from a string

    Args:
        s: a string containing PENMAN graphs
        model: the Xmrs subclass instantiated from decoded triples
    Returns:
        a list of objects (of class *model*)
    """
    graphs = penman.loads(s, cls=XMRSCodec)
    xs = [model.from_triples(g.triples()) for g in graphs]
    return xs


def dump(fh, xs, model=None, properties=False, indent=True, **kwargs):
    """
    Serialize [Xmrs] (or subclass) objects to PENMAN and write to a file

    Args:
        fh: filename or file object
        xs: an iterator of [Xmrs] objects to serialize
        model: the Xmrs subclass used to get triples
        properties: if True, encode variable properties
        indent: if True, adaptively indent; if False or None, don't
            indent; if a non-negative integer N, indent N spaces per level
        pretty_print: (deprecated) if set, it overrides indent
    Returns:
        None
    """
    text = dumps(
        xs, model=model, properties=properties, indent=indent, **kwargs
    )
    if hasattr(file, 'write'):
        print(text, file=file)
    else:
        with open(file, 'w') as fh:
            print(text, file=fh)


def dumps(xs, model=None, properties=False, indent=True, **kwargs):
    """
    Serialize [Xmrs] (or subclass) objects to PENMAN notation

    Args:
        xs: an iterator of [Xmrs] objects to serialize
        model: the Xmrs subclass used to get triples
        properties: if True, encode variable properties
        indent: if True, adaptively indent; if False or None, don't
            indent; if a non-negative integer N, indent N spaces per level
        pretty_print: (deprecated) if set, it overrides indent
    Returns:
        the PENMAN serialization of *xs*
    """
    xs = list(xs)
    
    if not xs:
        return ''

    if model is None:
        model = xs[0].__class__

    if not hasattr(model, 'to_triples'):
        raise TypeError(
            '{} class does not implement to_triples()'.format(model.__name__)
        )

    codec = XMRSCodec()
    graphs = [
        codec.triples_to_graph(
            model.to_triples(model.from_xmrs(x), properties=properties)
        )
        for x in xs
    ]

    if 'pretty_print' in kwargs:
        indent = kwargs['pretty_print']

    return penman.dumps(graphs, cls=XMRSCodec, indent=indent)


def _canonical_ids(ts):
    return ts # [(str(s), r, str(t)) for s, r, t in ts]
