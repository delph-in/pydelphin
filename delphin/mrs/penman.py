
r"""
Serialization functions for the PENMAN graph format.

Unlike other \*MRS serializers, this one takes a *model* argument for
the load(), loads(), dump(), and dumps() methods, which determines what
the graph will look like. This is because DMRS and EDS (and possibly
others in the future) yield different graph structures, but both can be
encoded as PENMAN graphs. In this sense, it is somewhat like how JSON
formatting of \*MRS is handled in PyDelphin.
"""

from __future__ import absolute_import, print_function

import penman

from delphin.mrs.config import LTOP_NODEID


class XMRSCodec(penman.PENMANCodec):
    r"""
    A customized PENMAN codec class for \*MRS data.
    """
    TYPE_REL = 'predicate'
    TOP_VAR = LTOP_NODEID
    TOP_REL = 'top'


def load(fh, model):
    """
    Deserialize PENMAN graphs from a file (handle or filename)

    Args:
        fh: filename or file object
        model: Xmrs subclass instantiated from decoded triples
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
        s (str): serialized PENMAN graphs
        model: Xmrs subclass instantiated from decoded triples
    Returns:
        a list of objects (of class *model*)
    """
    graphs = penman.loads(s, cls=XMRSCodec)
    xs = [model.from_triples(g.triples()) for g in graphs]
    return xs


def dump(destination, xs, model=None, properties=False, indent=True, **kwargs):
    """
    Serialize Xmrs (or subclass) objects to PENMAN and write to a file.

    Args:
        destination: filename or file object
        xs: iterator of :class:`~delphin.mrs.xmrs.Xmrs` objects to
            serialize
        model: Xmrs subclass used to get triples
        properties: if `True`, encode variable properties
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    """
    text = dumps(
        xs, model=model, properties=properties, indent=indent, **kwargs
    )
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w') as fh:
            print(text, file=fh)


def dumps(xs, model=None, properties=False, indent=True, **kwargs):
    """
    Serialize Xmrs (or subclass) objects to PENMAN notation

    Args:
        xs: iterator of :class:`~delphin.mrs.xmrs.Xmrs` objects to
            serialize
        model: Xmrs subclass used to get triples
        properties: if `True`, encode variable properties
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        the PENMAN serialization of *xs*
    """
    xs = list(xs)

    if not xs:
        return ''

    given_class = xs[0].__class__  # assume they are all the same
    if model is None:
        model = xs[0].__class__

    if not hasattr(model, 'to_triples'):
        raise TypeError(
            '{} class does not implement to_triples()'.format(model.__name__)
        )

    # convert MRS to DMRS if necessary; EDS cannot convert
    if given_class.__name__ in ('Mrs', 'Xmrs'):
        xs = [model.from_xmrs(x, **kwargs) for x in xs]
    elif given_class.__name__ == 'Eds' and model.__name__ != 'Eds':
        raise ValueError('Cannot convert EDS to non-EDS')

    codec = XMRSCodec()
    graphs = [
        codec.triples_to_graph(model.to_triples(x, properties=properties))
        for x in xs
    ]

    if 'pretty_print' in kwargs:
        indent = kwargs['pretty_print']

    return penman.dumps(graphs, cls=XMRSCodec, indent=indent)


def _canonical_ids(ts):
    return ts # [(str(s), r, str(t)) for s, r, t in ts]
