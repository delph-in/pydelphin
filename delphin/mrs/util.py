from itertools import chain, combinations
from operator import itemgetter
from networkx import DiGraph, relabel_nodes
from delphin._exceptions import XmrsStructureError


first = itemgetter(0)
second = itemgetter(1)


class AccumulationDict(dict):
    def __init__(self, accumulator, *args, **kwargs):
        if not hasattr(accumulator, '__call__'):
            raise TypeError('Accumulator must be a binary function.')
        self.accumulator = accumulator
        self.accumulate(*args, **kwargs)

    def __additem__(self, key, value):
        if key in self:
            self[key] = self.accumulator(self[key], value)
        else:
            self[key] = value

    def __add__(self, other):
        result = AccumulationDict(self.accumulator, self)
        result.accumulate(other)
        return result

    def accumulate(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, dict):
                arg = arg.items()
            if not hasattr(arg, '__iter__'):
                raise TypeError('{} object is not iterable'
                                .format(arg.__class__.__name__))
            for (key, value) in arg:
                self.__additem__(key, value)
        for key in kwargs:
            self.__additem__(key, kwargs[key])


def dict_of_dicts(triples, dicttype=dict):
    d = dicttype()
    for a, b, c in triples:
        try:
            d[a][b] = c
        except KeyError:
            d[a] = dicttype()
            d[a][b] = c
    return d


# adapted from recipe in itertools documentation
def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

class XmrsDiGraph(DiGraph):
    def __init__(self, data=None, name='', **attr):
        DiGraph.__init__(self, data=data, name=name, attr=attr)
        self.nodeids = [] if data is None else data.nodeids
        self.labels = set([] if data is None else data.labels)
        self.refresh()

    def refresh(self):
        seen = set()
        for nid in self.nodeids:
            n = self.node[nid]
            if n.get('iv') is not None:
                iv = n['iv']
                if iv not in self.node:
                    raise XmrsStructureError(
                        'Intrinsic variable ({}) of node {} is missing from '
                        'the Xmrs graph.'
                        .format(iv, nid)
                    )
                # clear the first time
                if iv not in seen:
                    self.node[iv]['bv'] = None
                    self.node[iv]['iv'] = None
                    seen.add(iv)
                if n['pred'].is_quantifier():
                    self.add_edge(iv, nid, {'bv': True})  # quantifier
                    self.node[iv]['bv'] = nid
                else:
                    self.add_edge(iv, nid, {'iv': True})  # intrinsic arg
                    self.node[iv]['iv'] = nid


    def subgraph(self, nbunch):
        nbunch = list(nbunch)
        sg = DiGraph.subgraph(self, nbunch)
        node = sg.node
        sg.nodeids = [nid for nid in nbunch if 'pred' in node[nid]]
        sg.labels = set(node[nid]['label'] for nid in nbunch
                        if 'label' in node[nid])
        g = XmrsDiGraph(sg)
        g.refresh()
        return g


    def relabel_nodes(self, mapping):
        g = relabel_nodes(self, mapping)
        # also need to fix where we store it ourselves
        for tnid in mapping.values():
            iv = g.node[tnid]['iv']
            if iv is not None:
                v = 'bv' if g.node[tnid]['pred'].is_quantifier() else 'iv'
                g.node[iv][v] = tnid
        g.nodeids = [mapping.get(n, n) for n in self.nodeids]
        g.labels = set(self.labels)
        return XmrsDiGraph(data=g)