
# DMRX codec
# Summary: This module implements serialization and deserialization of the XML
#          XML encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing single DMRX instances. Further,
#          encode_list and decode_list are provided for lists of DMRX
#          instances, and they read and write incrementally.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from collections import OrderedDict
import re
from delphin.mrs import (Dmrs, Node, Link, Pred, Lnk)
from delphin.mrs.config import (GRAMMARPRED, STRINGPRED, REALPRED,
                                QUANTIFIER_SORT)
from delphin._exceptions import MrsDecodeError

# Import LXML if available, otherwise fall back to another etree implementation
try:
  from lxml import etree
except ImportError:
  import xml.etree.ElementTree as etree

##############################################################################
##############################################################################
### Pickle-API methods

def load(fh):
    return decode(fh)

def loads(s):
    return decode_string(s)

def dump(fh, m, pretty_print=False):
    print(dumps(m, pretty_print=pretty_print), file=fh)

def dumps(m, pretty_print=False):
    return encode(m, pretty_print=pretty_print)

##############################################################################
##############################################################################
### Decoding

def decode_list(fh):
    """Decode """
    # <!ELEMENT dmrs-list (dmrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=('end')):
        yield decode_dmrs(elem)
        elem.clear()

def decode(fh):
    """Decode a DMRX-encoded DMRS structure."""
    elem = etree.parse(fh)
    return decode_dmrs(elem)

def decode_dmrs(elem):
    # <!ELEMENT dmrs (node|link)*>
    # <!ATTLIST dmrs
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.') # in case elem is an ElementTree rather than Element
    return Dmrs(nodes      = list(map(decode_node, elem.iter('node'))),
                links      = list(map(decode_link, elem.iter('link'))),
                lnk        = decode_lnk(elem),
                surface    = elem.get('surface'),
                identifier = elem.get('ident'))

def decode_node(elem):
    #<!ELEMENT node ((realpred|gpred), sortinfo)>
    #<!ATTLIST node
    #          nodeid CDATA #REQUIRED
    #          cfrom CDATA #REQUIRED
    #          cto   CDATA #REQUIRED
    #          surface   CDATA #IMPLIED
    #          base      CDATA #IMPLIED
    #          carg CDATA #IMPLIED >
    return Node(pred       = decode_pred(elem.find('./')),
                nodeid     = elem.get('nodeid'),
                sortinfo   = decode_sortinfo(elem.find('sortinfo')),
                lnk        = decode_lnk(elem),
                surface    = elem.get('surface'),
                base       = elem.get('base'),
                carg       = elem.get('carg'))

def decode_pred(elem):
    #<!ELEMENT realpred EMPTY>
    #<!ATTLIST realpred
    #          lemma CDATA #REQUIRED
    #          pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #          sense CDATA #IMPLIED >
    #<!ELEMENT gpred (#PCDATA)>
    if elem.tag == 'gpred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == 'realpred':
        return Pred.realpred(elem.get('lemma'),
                             elem.get('pos'),
                             elem.get('sense'))

def decode_sortinfo(elem):
    #<!ELEMENT sortinfo EMPTY>
    #<!ATTLIST sortinfo
    #          cvarsort (x|e|i|u) #IMPLIED
    #          num  (sg|pl|u) #IMPLIED
    #          pers (1|2|3|1-or-3|u) #IMPLIED
    #          gend (m|f|n|m-or-f|u) #IMPLIED
    #          sf (prop|ques|comm|prop-or-ques|u) #IMPLIED
    #          tense (past|pres|fut|tensed|untensed|u) #IMPLIED
    #          mood (indicative|subjunctive|u) #IMPLIED
    #          prontype (std_pron|zero_pron|refl|u) #IMPLIED
    #          prog (plus|minus|u) #IMPLIED
    #          perf (plus|minus|u) #IMPLIED
    #          ind  (plus|minus|u) #IMPLIED >
    # note: Just accept any properties, since these are ERG-specific
    return elem.attrib

def decode_link(elem):
    #<!ELEMENT link (rargname, post)>
    #<!ATTLIST link
    #          from CDATA #REQUIRED
    #          to   CDATA #REQUIRED >
    #<!ELEMENT rargname (#PCDATA)>
    #<!ELEMENT post (#PCDATA)>
    return Link(start   = elem.get('from'),
                end     = elem.get('to'),
                argname = elem.find('rargname').text,
                post    = elem.find('post').text)

def decode_lnk(elem):
    return Lnk.charspan(elem.get('cfrom'), elem.get('cto'))

##############################################################################
##############################################################################
### Encoding

_strict = False

def encode(m, strict=False, encoding='unicode', pretty_print=False):
    _strict = strict
    attributes = OrderedDict([('cfrom',str(m.cfrom)), ('cto',str(m.cto))])
    if m.surface is not None:    attributes['surface'] = m.surface
    if m.identifier is not None: attributes['ident']   = m.identifier
    if not _strict and m.index is not None:
        # index corresponds to a variable, so link it to a nodeid
        attributes['index'] = str(m.index.vid)
    # ltop link from 0
    #if m.ltop is not None:
    #
    e = etree.Element('dmrs', attrib=attributes)
    for node in m.nodes: e.append(encode_node(node))
    for link in m.links: e.append(encode_link(link))
    # for now, pretty_print=True is the same as pretty_print='LKB'
    if pretty_print in ('LKB', 'lkb', 'Lkb', True):
        lkb_pprint_re = re.compile(r'(<dmrs[^>]+>|</node>|</link>|</dmrs>)')
        string = str(etree.tostring(e, encoding=encoding))
        return lkb_pprint_re.sub(r'\1\n', string)
    # pretty_print is only lxml. Look into tostringlist, maybe?
    #return etree.tostring(e, pretty_print=pretty_print, encoding='unicode')
    return etree.tostring(e, encoding=encoding)

def encode_node(node):
    attributes = OrderedDict([('nodeid', str(node.nodeid)),
                              ('cfrom',str(node.cfrom)),
                              ('cto',str(node.cto))])
    if node.surface is not None: attributes['surface'] = node.surface
    if node.base is not None:    attributes['base']    = node.base
    if node.carg is not None:    attributes['carg']    = node.carg
    e = etree.Element('node', attrib=attributes)
    e.append(encode_pred(node.pred))
    e.append(encode_sortinfo(node))
    return e

def encode_pred(pred):
    if pred.type == GRAMMARPRED:
        e = etree.Element('gpred')
        e.text = pred.string.strip('"\'')
    elif pred.type in (REALPRED, STRINGPRED):
        attributes = {}
        if pred.lemma is not None:
            attributes['lemma'] = pred.lemma
        if pred.pos is not None:
            attributes['pos'] = pred.pos
        if pred.sense is not None:
            attributes['sense'] = str(pred.sense)
        e = etree.Element('realpred', attrib=attributes)
    return e

def encode_sortinfo(node):
    attributes = OrderedDict()
    # return empty <sortinfo/> for quantifiers
    if node.pred.pos == QUANTIFIER_SORT:
        return etree.Element('sortinfo') # return empty <sortinfo/>
    if node.sortinfo:
        if not _strict:
            for k, v in node.sortinfo.items():
                attributes[k.lower()] = str(v)
        else:
            pass #TODO add strict sortinfo
    e = etree.Element('sortinfo', attrib=attributes or {})
    return e

def encode_link(link):
    e = etree.Element('link', attrib={'from':str(link.start),
                                      'to':str(link.end)})
    argname = etree.Element('rargname')
    argname.text = link.argname
    post = etree.Element('post')
    post.text = link.post
    e.append(argname)
    e.append(post)
    return e
