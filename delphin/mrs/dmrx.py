
"""
DMRX (XML for DMRS) serialization and deserialization.
"""

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
    """
    Deserialize DMRX from a file (handle or filename)

    Args:
        fh (str, file): input filename or file object
        single: if `True`, only return the first read Xmrs object
    Returns:
        a generator of Xmrs objects (unless the *single* option is
        `True`)
    """
    ms = deserialize(fh)
    if single:
        ms = next(ms)
    return ms


def loads(s, single=False):
    """
    Deserialize DMRX string representations

    Args:
        s (str): a DMRX string
        single (bool): if `True`, only return the first Xmrs object
    Returns:
        a generator of Xmrs objects (unless *single* is `True`)
    """
    corpus = etree.fromstring(s)
    if single:
        ds = _deserialize_dmrs(next(iter(corpus)))
    else:
        ds = (_deserialize_dmrs(dmrs_elem) for dmrs_elem in corpus)
    return ds


def dump(destination, ms, single=False, properties=True, pretty_print=False, **kwargs):
    """
    Serialize Xmrs objects to DMRX and write to a file

    Args:
        destination: filename or file object where data will be written
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object
            instead of as an iterator
        properties: if `False`, suppress variable properties
        pretty_print: if `True`, add newlines and indentation
    """
    text = dumps(ms,
                 single=single,
                 properties=properties,
                 pretty_print=pretty_print,
                 **kwargs)

    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w') as fh:
            print(text, file=fh)


def dumps(ms, single=False, properties=True, pretty_print=False, **kwargs):
    """
    Serialize an Xmrs object to a DMRX representation

    Args:
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object instead
            of as an iterator
        properties: if `False`, suppress variable properties
        pretty_print: if `True`, add newlines and indentation
    Returns:
        a DMRX string representation of a corpus of Xmrs
    """
    if not pretty_print and kwargs.get('indent'):
        pretty_print = True
    if single:
        ms = [ms]
    return serialize(ms, properties=properties, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

def deserialize(fh):
    # <!ELEMENT dmrs-list (dmrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for _, elem in etree.iterparse(fh, events=('end',)):
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
                top=elem.get('top'),
                index=elem.get('index'),
                xarg=elem.get('xarg'),
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
                nodeid=elem.get('nodeid'),
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
        return Pred.abstract(elem.text)
    elif elem.tag == 'realpred':
        return Pred.realpred(elem.get('lemma'),
                             elem.get('pos') or None,
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


def serialize(ms, properties=True, encoding='unicode', pretty_print=False):
    e = etree.Element('dmrs-list')
    for m in ms:
        e.append(_encode_dmrs(m, properties))
    # for now, pretty_print=True is the same as pretty_print='LKB'
    if pretty_print in ('LKB', 'lkb', 'Lkb', True):
        lkb_pprint_re = re.compile(r'(<dmrs[^>]+>|</node>|</link>|</dmrs>)')
        string = str(etree_tostring(e, encoding=encoding))
        return lkb_pprint_re.sub(r'\1\n', string)
    # pretty_print is only lxml. Look into tostringlist, maybe?
    # return etree.tostring(e, pretty_print=pretty_print, encoding='unicode')
    return etree_tostring(e, encoding=encoding)


def _encode_dmrs(m, properties):
    attributes = OrderedDict([('cfrom', str(m.cfrom)),
                              ('cto', str(m.cto))])
    # if m.top is not None: ... currently handled by links()
    if m.index is not None:
        idx = m.nodeid(m.index)
        if idx is not None:
            attributes['index'] = str(idx)
    if m.xarg is not None:
        xarg = m.nodeid(m.xarg)
        if xarg is not None:
            attributes['xarg'] = str(xarg)
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    e = etree.Element('dmrs', attrib=attributes)
    for node in nodes(m):
        e.append(_encode_node(node, properties))
    for link in links(m):
        e.append(_encode_link(link))
    return e


def _encode_node(node, properties):
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
    e.append(_encode_sortinfo(node, properties))
    return e


def _encode_pred(pred):
    if pred.type == Pred.ABSTRACT:
        e = etree.Element('gpred')
        e.text = pred.string.strip('"\'')
    elif pred.type in (Pred.REALPRED, Pred.SURFACE):
        attributes = {}
        attributes['lemma'] = pred.lemma
        if pred.pos is None:
            attributes['pos'] = ""
        else:
            attributes['pos'] = pred.pos
        if pred.sense is not None:
            attributes['sense'] = str(pred.sense)
        e = etree.Element('realpred', attrib=attributes)
    return e


def _encode_sortinfo(node, properties):
    attributes = OrderedDict()
    # return empty <sortinfo/> for quantifiers
    if node.pred.pos == QUANTIFIER_POS:
        return etree.Element('sortinfo')  # return empty <sortinfo/>
    if properties and node.sortinfo:
        for k, v in node.sortinfo.items():
            attributes[k.lower()] = str(v)
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
