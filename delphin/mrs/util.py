from itertools import chain, combinations
from operator import itemgetter
from networkx import DiGraph

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

    def subgraph(self, nbunch):
        sg = DiGraph.subgraph(self, nbunch)
        node = sg.node
        sg.nodeids = [nid for nid in nbunch if 'ep' in node[nid]]
        sg.labels = set(node[nid]['label'] for nid in nbunch
                        if 'label' in node[nid])
        return XmrsDiGraph(sg)