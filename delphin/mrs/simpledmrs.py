
# SimpleDMRS codec
# Summary: This module implements serialization and deserialization of the
#          SimpleDMRS encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing single SimpleDMRS instances. Further,
#          encode_list and decode_list are provided for lists of DMRX
#          instances, and they read and write incrementally.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function

from collections import OrderedDict
from io import BytesIO
import re
from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.components import (nodes, links)
from delphin.mrs.config import EQ_POST, CVARSORT


##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    ms = decode(fh)
    if single:
        ms = next(ms)
    return ms


def loads(s, single=False, encoding='utf-8'):
    ms = decode(BytesIO(bytes(s, encoding=encoding)))
    if single:
        ms = next(ms)
    return ms


def dump(fh, ms, **kwargs):
    print(dumps(ms, **kwargs), file=fh)


def dumps(ms, single=False, pretty_print=False, **kwargs):
    if single:
        ms = [ms]
    return encode(ms, indent=2 if pretty_print else None)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

tokenizer = re.compile(r'("[^"\\]*(?:\\.[^"\\]*)*"'
                       r'|[^\s:#@\[\]<>"]+'
                       r'|[:#@\[\]<>])')

def decode(fh):
    """Decode a SimpleDmrs-encoded DMRS structure."""
    # (dmrs { ... })*

def decode_dmrs(elem):
    # dmrs { NODES LINKS }
    return Dmrs(nodes=list(map(decode_node)),
                links=list(map(decode_link)),
                lnk=None,
                surface=None,
                identifier=None)


def decode_node(elem):
    return Node(pred=decode_pred(elem.find('*[1]')),
                nodeid=elem.get('nodeid'),
                sortinfo=decode_sortinfo(elem.find('sortinfo')),
                lnk=decode_lnk(elem),
                surface=elem.get('surface'),
                base=elem.get('base'),
                carg=elem.get('carg'))


def decode_pred(elem):
    if elem.tag == 'gpred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == 'realpred':
        return Pred.realpred(elem.get('lemma'),
                             elem.get('pos'),
                             elem.get('sense'))


def decode_sortinfo(elem):
    return elem.attrib


def decode_link(elem):
    return Link(start=elem.get('from'),
                end=elem.get('to'),
                rargname=elem.find('rargname').text,
                post=elem.find('post').text)


def decode_lnk(elem):
    return Lnk.charspan(elem.get('cfrom', '-1'), elem.get('cto', '-1'))

##############################################################################
##############################################################################
# Encoding

_graphtype = 'dmrs'
_graph = '{graphtype} {graphid}{{{dmrsproperties}{nodes}{links}}}'
_dmrsproperties = ''
_node = '{indent}{nodeid} [{pred}{lnk}{sortinfo}];'
_sortinfo = ' {cvarsort} {properties}'
_link = '{indent}{start}:{pre}/{post} {arrow} {end};'

def encode(ms, encoding='unicode', indent=2):
    delim = '\n' if indent is not None else ' '
    return delim.join(encode_dmrs(m, indent=indent) for m in ms)

def encode_dmrs(m, indent=2):
    if indent is not None:
        delim = '\n'
        space = ' ' * indent
    else:
        delim = ''
        space = ' '

    nodes_ = [
        _node.format(
            indent=space,
            nodeid=n.nodeid,
            pred=n.pred.string,
            lnk='' if n.lnk is None else str(n.lnk),
            sortinfo=(
                '' if not n.sortinfo else
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

    links_ = [
        _link.format(
            indent=space,
            start=l.start,
            pre=l.rargname or '',
            post=l.post,
            arrow='->' if l.rargname or l.post != EQ_POST else '--',
            end=l.end
        )
        for l in links(m)
    ]

    return delim.join(['dmrs {'] + nodes_ + links_ + ['}'])
