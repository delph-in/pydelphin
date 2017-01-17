
# DMRX codec
# Summary: This module implements serialization and deserialization of the
#          XML encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing DMRX corpora. Further,
#          load_one, loads_one, dump_one, and dumps_one operate on a single
#          DMRX/DMRS.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function

from collections import OrderedDict
import re
import xml.etree.ElementTree as etree

from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.components import (nodes, links)
from delphin.mrs.config import QUANTIFIER_POS
from delphin.mrs.util import etree_tostring

##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    ms = deserialize(fh)
    if single:
        ms = next(ms)
    return ms


def loads(s, single=False):
    corpus = etree.fromstring(s)
    if single:
        ds = _deserialize_dmrs(next(iter(corpus)))
    else:
        ds = (_deserialize_dmrs(dmrs_elem) for dmrs_elem in corpus)
    return ds


def dump(fh, ms, **kwargs):
    print(dumps(ms, **kwargs), file=fh)


def dumps(ms, single=False, pretty_print=False, **kwargs):
    if not pretty_print and kwargs.get('indent'):
        pretty_print = True
    if single:
        ms = [ms]
    return serialize(ms, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

def deserialize(fh):
    """Deserialize a DMRX-encoded DMRS structure."""
    # <!ELEMENT dmrs-list (dmrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=('end',)):
        if elem.tag == 'dmrs':
            yield _deserialize_dmrs(elem)
            elem.clear()

def _deserialize_dmrs(elem):
    # <!ELEMENT dmrs (node|link)*>
    # <!ATTLIST dmrs
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.')  # in case elem is an ElementTree rather than Element
    return Dmrs(nodes=list(map(_decode_node, elem.iter('node'))),
                links=list(map(_decode_link, elem.iter('link'))),
                lnk=_decode_lnk(elem),
                surface=elem.get('surface'),
                identifier=elem.get('ident'))


def _decode_node(elem):
    # <!ELEMENT node ((realpred|gpred), sortinfo)>
    # <!ATTLIST node
    #           nodeid CDATA #REQUIRED
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED
    #           carg CDATA #IMPLIED >
    return Node(pred=_decode_pred(elem.find('*[1]')),
                nodeid=int(elem.get('nodeid')),
                sortinfo=_decode_sortinfo(elem.find('sortinfo')),
                lnk=_decode_lnk(elem),
                surface=elem.get('surface'),
                base=elem.get('base'),
                carg=elem.get('carg'))


def _decode_pred(elem):
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


def _decode_sortinfo(elem):
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


def _decode_link(elem):
    # <!ELEMENT link (rargname, post)>
    # <!ATTLIST link
    #           from CDATA #REQUIRED
    #           to   CDATA #REQUIRED >
    # <!ELEMENT rargname (#PCDATA)>
    # <!ELEMENT post (#PCDATA)>
    return Link(start=elem.get('from'),
                end=elem.get('to'),
                rargname=getattr(elem.find('rargname'), 'text', None),
                post=getattr(elem.find('post'), 'text', None))


def _decode_lnk(elem):
    return Lnk.charspan(elem.get('cfrom', '-1'), elem.get('cto', '-1'))

##############################################################################
##############################################################################
# Encoding

_strict = False


def serialize(ms, strict=False, encoding='unicode', pretty_print=False):
    e = etree.Element('dmrs-list')
    for m in ms:
        e.append(_encode_dmrs(m, strict=strict))
    # for now, pretty_print=True is the same as pretty_print='LKB'
    if pretty_print in ('LKB', 'lkb', 'Lkb', True):
        lkb_pprint_re = re.compile(r'(<dmrs[^>]+>|</node>|</link>|</dmrs>)')
        string = str(etree_tostring(e, encoding=encoding))
        return lkb_pprint_re.sub(r'\1\n', string)
    # pretty_print is only lxml. Look into tostringlist, maybe?
    # return etree.tostring(e, pretty_print=pretty_print, encoding='unicode')
    return etree_tostring(e, encoding=encoding)


def _encode_dmrs(m, strict=False):
    _strict = strict
    attributes = OrderedDict([('cfrom', str(m.cfrom)),
                              ('cto', str(m.cto))])
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    # if not _strict and m.index is not None:
    #     # index corresponds to a variable, so link it to a nodeid
    #     index_nodeid = m.get_nodeid(m.index)
    #     if index_nodeid is not None:
    #         attributes['index'] = str(index_nodeid)
    e = etree.Element('dmrs', attrib=attributes)
    for node in nodes(m):
        e.append(_encode_node(node))
    for link in links(m):
        e.append(_encode_link(link))
    return e


def _encode_node(node):
    attributes = OrderedDict([('nodeid', str(node.nodeid)),
                              ('cfrom', str(node.cfrom)),
                              ('cto', str(node.cto))])
    if node.surface is not None:
        attributes['surface'] = node.surface
    if node.base is not None:
        attributes['base'] = node.base
    if node.carg is not None:
        attributes['carg'] = node.carg
    e = etree.Element('node', attrib=attributes)
    e.append(_encode_pred(node.pred))
    e.append(_encode_sortinfo(node))
    return e


def _encode_pred(pred):
    if pred.type == Pred.GRAMMARPRED:
        e = etree.Element('gpred')
        e.text = pred.string.strip('"\'')
    elif pred.type in (Pred.REALPRED, Pred.STRINGPRED):
        attributes = {}
        if pred.lemma is not None:
            attributes['lemma'] = pred.lemma
        if pred.pos is not None:
            attributes['pos'] = pred.pos
        if pred.sense is not None:
            attributes['sense'] = str(pred.sense)
        e = etree.Element('realpred', attrib=attributes)
    return e


def _encode_sortinfo(node):
    attributes = OrderedDict()
    # return empty <sortinfo/> for quantifiers
    if node.pred.pos == QUANTIFIER_POS:
        return etree.Element('sortinfo')  # return empty <sortinfo/>
    if node.sortinfo:
        if not _strict:
            for k, v in node.sortinfo.items():
                attributes[k.lower()] = str(v)
        else:
            pass  # TODO add strict sortinfo
    e = etree.Element('sortinfo', attrib=attributes or {})
    return e


def _encode_link(link):
    e = etree.Element('link', attrib={'from': str(link.start),
                                      'to': str(link.end)})
    rargname = etree.Element('rargname')
    rargname.text = link.rargname
    post = etree.Element('post')
    post.text = link.post
    e.append(rargname)
    e.append(post)
    return e
