
# SimpleDMRS codec
# Summary: This module implements serialization and deserialization of the
#          SimpleDMRS encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing single SimpleDMRS instances. Further,
#          encode_list and decode_list are provided for lists of DMRX
#          instances, and they read and write incrementally.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
from io import BytesIO
import re
from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.config import (QUANTIFIER_SORT, EQ_POST)


_graphtype = 'dmrs'
_graph = '{graphtype} {graphid}{{{dmrsproperties}{nodes}{links}}}'
_dmrsproperties = ''
_node = '{nodeid} [{pred}{lnk}{sortinfo}];'
_sortinfo = ' {cvarsort} {properties}'
_link = '{from}:{pre}/{post} {arrow} {to};'

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
    return encode(ms, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

def decode(fh):
    """Decode a DMRX-encoded DMRS structure."""
    # <!ELEMENT dmrs-list (dmrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=('end',)):
        if elem.tag == 'dmrs':
            yield decode_dmrs(elem)
            elem.clear()

def decode_dmrs(elem):
    # <!ELEMENT dmrs (node|link)*>
    # <!ATTLIST dmrs
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.')  # in case elem is an ElementTree rather than Element
    return Dmrs(nodes=list(map(decode_node, elem.iter('node'))),
                links=list(map(decode_link, elem.iter('link'))),
                lnk=decode_lnk(elem),
                surface=elem.get('surface'),
                identifier=elem.get('ident'))


def decode_node(elem):
    # <!ELEMENT node ((realpred|gpred), sortinfo)>
    # <!ATTLIST node
    #           nodeid CDATA #REQUIRED
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED
    #           carg CDATA #IMPLIED >
    return Node(pred=decode_pred(elem.find('*[1]')),
                nodeid=elem.get('nodeid'),
                sortinfo=decode_sortinfo(elem.find('sortinfo')),
                lnk=decode_lnk(elem),
                surface=elem.get('surface'),
                base=elem.get('base'),
                carg=elem.get('carg'))


def decode_pred(elem):
    # <!ELEMENT realpred EMPTY>
    # <!ATTLIST realpred
    #           lemma CDATA #REQUIRED
    #           pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #           sense CDATA #IMPLIED >
    # <!ELEMENT gpred (#PCDATA)>
    if elem.tag == 'gpred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == 'realpred':
        return Pred.realpred(elem.get('lemma'),
                             elem.get('pos'),
                             elem.get('sense'))


def decode_sortinfo(elem):
    # <!ELEMENT sortinfo EMPTY>
    # <!ATTLIST sortinfo
    #           cvarsort (x|e|i|u) #IMPLIED
    #           num  (sg|pl|u) #IMPLIED
    #           pers (1|2|3|1-or-3|u) #IMPLIED
    #           gend (m|f|n|m-or-f|u) #IMPLIED
    #           sf (prop|ques|comm|prop-or-ques|u) #IMPLIED
    #           tense (past|pres|fut|tensed|untensed|u) #IMPLIED
    #           mood (indicative|subjunctive|u) #IMPLIED
    #           prontype (std_pron|zero_pron|refl|u) #IMPLIED
    #           prog (plus|minus|u) #IMPLIED
    #           perf (plus|minus|u) #IMPLIED
    #           ind  (plus|minus|u) #IMPLIED >
    # note: Just accept any properties, since these are ERG-specific
    return elem.attrib


def decode_link(elem):
    # <!ELEMENT link (rargname, post)>
    # <!ATTLIST link
    #           from CDATA #REQUIRED
    #           to   CDATA #REQUIRED >
    # <!ELEMENT rargname (#PCDATA)>
    # <!ELEMENT post (#PCDATA)>
    return Link(start=elem.get('from'),
                end=elem.get('to'),
                argname=elem.find('rargname').text,
                post=elem.find('post').text)


def decode_lnk(elem):
    return Lnk.charspan(elem.get('cfrom', '-1'), elem.get('cto', '-1'))

##############################################################################
##############################################################################
# Encoding

_strict = False

def encode(ms, strict=False, encoding='unicode', pretty_print=False, indent=2):
    ss = []
    for m in ms:
        s = _graph.format(**{
            'graphtype': _graphtype,
            'graphid': '',
            'dmrsproperties': _dmrsproperties.format(str(m.lnk)),
            'nodes': ''.join(_node.format(**{
                'nodeid': n.nodeid,
                'pred': str(n.pred),
                'lnk': '' if n.lnk is None else str(n.lnk),
                'sortinfo': '' if not n.sortinfo else _sortinfo.format(**{
                    'cvarsort': n.cvarsort,
                    'properties': ' '.join('{}={}'.format(k, v)
                                           for k, v in n.properties.items())
                    })
                })
                for n in m.nodes),
            'links': ''.join(_link.format(**{
                'from': l.start,
                'pre': l.argname or '',
                'post': l.post,
                'arrow': '->' if l.argname or l.post != EQ_POST else '--',
                'to': l.end
                })
                for l in m.links)
            })
        s = s.replace(';',';\n  ').replace('{','{\n  ').replace('  }','}')
        ss.append(s)
    return '\n'.join(ss)
