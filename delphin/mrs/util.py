from itertools import chain, combinations
from operator import itemgetter
from delphin.exceptions import XmrsStructureError


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


# used for getting variable properties
class ReadOnceDict(dict):
    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        del self[key]
        return val

    def get(self, key, default=None):
        if key in self:
            val = dict.__getitem__(self, key)
            del self[key]
        else:
            val = default
        return val


# adapted from recipe in itertools documentation
def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))


def rargname_sortkey(rargname):
    # canonical order: LBL ARG* RSTR BODY *-INDEX *-HNDL CARG ...
    rargname = rargname.upper()
    return (
        rargname != 'LBL',
        rargname in ('BODY', 'CARG'),
        # rargname.endswith('HNDL'),
        rargname
    )


# Python2 doesn't have 'unicode' as an encoding option, so fake it
# (inefficiently, but oh well)
import xml.etree.ElementTree as etree
try:
    etree.tostring(etree.Element('tag'), encoding='unicode')
    etree_tostring = etree.tostring
except LookupError:
    def etree_tostring(elem, encoding='unicode', **kwargs):
        _etree_str_to_unicode(elem)
        if encoding == 'unicode':
            return etree.tostring(elem, encoding='utf-8', **kwargs).decode('utf-8')
        else:
            return etree.tostring(elem, encoding=encoding, **kwargs)

def _etree_str_to_unicode(e, encoding='utf-8'):
    if isinstance(e.tag, str):
        e.tag = unicode(e.tag, encoding)
    if isinstance(e.text, str):
        e.text = unicode(e.text, encoding)
    if isinstance(e.tail, str):
        e.tail = unicode(e.tail, encoding)
    for attr, val in list(e.attrib.items()):
        del e.attrib[attr]
        if isinstance(attr, str):
            attr = unicode(attr, encoding)
        if isinstance(val, str):
            val = unicode(val, encoding)
        e.attrib[attr] = val
    for child in e:
        _etree_str_to_unicode(child, encoding)
