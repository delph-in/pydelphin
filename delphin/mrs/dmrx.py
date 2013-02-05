
# DMRX codec
# Summary: This module implements serialization and deserialization of the XML
#          XML encoding of Distributed Minimal Recusion Semantics (DMRS). It
#          provides standard Pickle API calls of load, loads, dump, and dumps
#          for serializing and deserializing single DMRX instances.  Further,
#          encode_list and decode_list are provided for lists of DMRX
#          instances, and they read and write incrementally.
#
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from . import mrs
from .mrserrors import MrsDecodeError

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

def dump(fh, m):
    fh.write(dumps(m))

def dumps(m):
    return encode(m)

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
    return mrs.Mrs(ltop = decode_label(elem.find('label')),
                   index = decode_var(elem.find('var')),
                   rels = [decode_ep(ep) for ep in elem.iter('ep')],
                   hcons = [decode_hcons(h) for h in elem.iter('hcons')],
                   link = decode_link(elem.get('cfrom'), elem.get('cto')),
                   surface = elem.get('surface'),
                   identifier = elem.get('ident'))

##############################################################################
##############################################################################
### Decoding

def encode_dmrs(m, strict=False):
    attributes = {'cfrom':str(m.cfrom), 'cto':str(m.cto)}
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    if not strict:
        attributes['ltop'] = m.ltop
        attributes['index'] = m.index.name
    e = etree.Element('dmrs', attrib=attributes)
    for ep in m.rels:
        e.append(encode_node(ep))
    return etree.tostring(e).decode('utf-8')

def encode_node(ep):
    attributes = {'nodeid':str(mrs.sort_vid_split(ep.label)[1]),
                  'cfrom':str(ep.cfrom), 'cto':str(ep.cto)}
    if ep.surface is not None:
        attributes['surface'] = ep.surface
    if ep.base is not None:
        attributes['base'] = ep.base
    carg = [a for a in ep.args.values() if not isinstance(a, mrs.MrsVariable)]
    if carg != []:
        # there should be only one constant
        attributes['carg'] = next(carg)
    e = etree.Element('node', attrib=attributes)
    e.append(encode_pred(ep.pred))
    # e.append(encode_sortinfo())
    return e

def encode_pred(pred):
    name = pred.string.strip('"\'')
    if pred.type == mrs.Pred.GPRED:
        return etree.Element('gpred', name=name)
    elif pred.type in (mrs.Pred.REALPRED, mrs.Pred.SPRED):
        return etree.Element('realpred', name=name)
