
"""
Serialization for the SimpleDMRS format.

Note that this format is provided by PyDelphin and not defined
anywhere, so it should only be used for user's convenience and not
used as an interchange format or for other practical purposes. It was
created with human legibility in mind (e.g. for investigating DMRSs
at the command line, because XML (DMRX) is not easy to read).
Deserialization is not provided.
"""

from __future__ import print_function

from collections import OrderedDict
from io import BytesIO
import re
from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.components import (nodes, links)
from delphin.mrs.config import EQ_POST, CVARSORT, CONSTARG_ROLE


##############################################################################
##############################################################################
# Pickle-API methods


# def load(fh, single=False):
#     ms = deserialize(fh)
#     if single:
#         ms = next(ms)
#     return ms


# def loads(s, single=False, encoding='utf-8'):
#     ms = deserialize(BytesIO(bytes(s, encoding=encoding)))
#     if single:
#         ms = next(ms)
#     return ms


def dump(destination, ms, **kwargs):
    text = dumps(ms, **kwargs)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w') as fh:
            print(text, file=fh)


def dumps(ms, single=False, properties=True, pretty_print=False, **kwargs):
    if pretty_print and 'indent' not in kwargs:
        kwargs['indent'] = 2
    if single:
        ms = [ms]
    return serialize(ms, properties=properties, indent=kwargs.get('indent'))

# for convenience

# load_one = lambda fh: load(fh, single=True)
# loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

# tokenizer = re.compile(r'("[^"\\]*(?:\\.[^"\\]*)*"'
#                        r'|[^\s:#@\[\]<>"]+'
#                        r'|[:#@\[\]<>])')

# def deserialize(fh):
#     """deserialize a SimpleDmrs-encoded DMRS structure."""
#     raise NotImplementedError

##############################################################################
##############################################################################
# Encoding

_graphtype = 'dmrs'
_graph = '{graphtype} {graphid}{{{dmrsproperties}{nodes}{links}}}'
_dmrsproperties = ''
_node = '{indent}{nodeid} [{pred}{lnk}{carg}{sortinfo}];'
_sortinfo = ' {cvarsort} {properties}'
_link = '{indent}{start}:{pre}/{post} {arrow} {end};'

def serialize(ms, properties=True, encoding='unicode', indent=2):
    delim = '\n' if indent is not None else ' '
    return delim.join(_encode_dmrs(m, properties, indent=indent) for m in ms)

def _encode_dmrs(m, properties, indent=2):
    if indent is not None:
        delim = '\n'
        space = ' ' * indent
    else:
        delim = ''
        space = ' '

    attrs = []

    nodes_ = [
        _node.format(
            indent=space,
            nodeid=n.nodeid,
            pred=n.pred.string,
            lnk='' if n.lnk is None else str(n.lnk),
            carg='' if n.carg is None else '("{}")'.format(n.carg),
            sortinfo=(
                '' if not (properties and n.sortinfo) else
                _sortinfo.format(
                    cvarsort=n.cvarsort,
                    properties=' '.join('{}={}'.format(k, v)
                                        for k, v in n.sortinfo.items()
                                        if k != CVARSORT),
                )
            )
        )
        for n in nodes(m)
    ]

    links_ = []
    for l in links(m):
        if l.start == 0:
            attrs.append('top={}'.format(l.end))
        else:
            links_.append(
                _link.format(
                    indent=space,
                    start=l.start,
                    pre=l.rargname or '',
                    post=l.post,
                    arrow='->' if l.rargname or l.post != EQ_POST else '--',
                    end=l.end
                )
            )

    if m.index is not None:
        idx = m.nodeid(m.index)
        if idx is not None:
            attrs.append('index={}'.format(idx))
    if m.lnk is not None:
        attrs.append('lnk={}'.format(str(m.lnk)))
    if m.surface is not None:
        attrs.append('surface="{}"'.format(m.surface))

    if attrs:
        attrs = ['{}[{}]'.format(space, ' '.join(attrs))]

    return delim.join(['dmrs {'] + attrs + nodes_ + links_ + ['}'])
