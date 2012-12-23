
# MRX codec
# Summary: This module implements serialization and deserialization of
#          the XML encoding of Minimal Recusion Semantics. It provides
#          standard Pickle API calls of load, loads, dump, and dumps for
#          serializing and deserializing single MRX instances.
#          Further, encode_list and decode_list are provided for lists
#          of MRX instances, and they read and write incrementally.
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

HANDLE_PREFIX = 'h'

def decode_list(fh):
    """Decode """
    # <!ELEMENT mrs-list (mrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=('end')):
        yield decode_mrs(elem)
        elem.clear()

def decode(fh):
    """Decode an MRX-encoded MRS structure."""
    elem = etree.parse(fh)
    return decode_mrs(elem)

def decode_mrs(elem):
    # <!ELEMENT mrs (label, var, (ep|hcons)*)>
    # <!ATTLIST mrs
    #           cfrom     CDATA #IMPLIED
    #           cto       CDATA #IMPLIED 
    #           surface   CDATA #IMPLIED 
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.') # in case elem is an ElementTree rather than Element
    normalize_vars(elem) # try to make all vars have a sort
    return mrs.Mrs(ltop = decode_label(elem.find('label')),
                   index = decode_var(elem.find('var')),
                   rels = [decode_ep(ep) for ep in elem.iter('ep')],
                   hcons = [decode_hcons(h) for h in elem.iter('hcons')],
                   link = decode_link(elem.get('cfrom'), elem.get('cto')),
                   surface = elem.get('surface'),
                   identifier = elem.get('ident'))

def normalize_vars(elem):
    # vars are in 3 places, top of MRS, arg of fvpair, and args of hcons
    vars = [elem.find('var')] + elem.findall('ep/fvpair/var') +\
           elem.findall('hcons//var')
    vid_sort = dict((v.get('vid'), v.get('sort')) for v in vars
                    if v.get('sort') is not None)
    for v in vars:
        if v.get('sort') is None:
            v.set('sort', vid_sort.get(v.get('vid')))

def decode_label(elem):
    # <!ELEMENT label (extrapair*)>
    # <!ATTLIST label 
    #           vid CDATA #REQUIRED >
    # NOTE: I deviate from the DTD here by not retrieving extrapairs;
    #       as far as I can tell handles cannot take properties
    return decode_handle(elem)

def decode_handle(elem):
    # Both label and var elements have a 'vid' attribute.
    # For compatibility, add the HANDLE_PREFIX ('h') to the vid (e.g. 'h1')
    return HANDLE_PREFIX + elem.get('vid')

def decode_var(elem):
    # <!ELEMENT var (extrapair*)>
    # <!ATTLIST var
    #           vid  CDATA #REQUIRED 
    #           sort (x|e|h|u|l|i) #IMPLIED >
    return mrs.MrsVariable(vid=int(elem.get('vid')), sort=elem.get('sort'),
                           props=decode_extrapairs(elem.iter('extrapair')))

def decode_extrapairs(elems):
    # <!ELEMENT extrapair (path,value)>
    # <!ELEMENT path (#PCDATA)>
    # <!ELEMENT value (#PCDATA)>
    return dict((e.find('path').text, e.find('value').text) for e in elems)

def decode_ep(elem):
    # <!ELEMENT ep ((pred|spred|realpred), label, fvpair*)>
    # <!ATTLIST ep
    #           cfrom CDATA #IMPLIED
    #           cto   CDATA #IMPLIED 
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED >
    return mrs.ElementaryPredication(pred=decode_pred(elem.find('./')),
                                     label=decode_label(elem.find('label')),
                                     scargs=decode_scargs(elem),
                                     args=decode_args(elem),
                                     link=decode_link(elem.get('cfrom'),
                                                      elem.get('cto')),
                                     surface=elem.get('surface'),
                                     base=elem.get('base'))

def decode_pred(elem):
    # <!ELEMENT pred (#PCDATA)>
    # <!ELEMENT spred (#PCDATA)>
    # <!ELEMENT realpred EMPTY>
    # <!ATTLIST realpred
    #           lemma CDATA #REQUIRED
    #           pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #           sense CDATA #IMPLIED >
    if elem.tag in ('pred', 'spred'):
        return mrs.Pred(elem.text)
    elif elem.tag == 'realpred':
        return mrs.Pred(lemma=elem.get('lemma'),
                        pos=elem.get('pos'),
                        sense=elem.get('sense'))

def decode_scargs(elem):
    # <!ELEMENT fvpair (rargname, (var|constant))>
    # scopal args have sort 'h', so we're only interested when the
    # second element is a var
    return dict((e.find('rargname').text, decode_handle(e.find('var')))
                for e in elem.findall('fvpair/var/[@sort="h"]..'))

def decode_args(elem):
    # <!ELEMENT fvpair (rargname, (var|constant))>
    # non-scopal args are anything that isn't a var with sort='h'
    args = {}
    for e in elem.findall('fvpair'):
        argname = e.find('rargname').text
        if e.find('constant') is not None:
            args[argname] = e.find('constant').text
        elif e.find('var').get('sort') != 'h':
            args[argname] = decode_var(e.find('var'))
    return args

def decode_hcons(elem):
    # <!ELEMENT hcons (hi, lo)>
    # <!ATTLIST hcons 
    #           hreln (qeq|lheq|outscopes) #REQUIRED >
    # <!ELEMENT hi (var)>
    # <!ELEMENT lo (label|var)>
    # As with scopal args, I assume any vars in hcons have sort='h', and are
    # thus handles without variable properties
    return mrs.HandleConstraint(decode_handle(elem.find('hi/')),
                                elem.get('hreln'),
                                decode_handle(elem.find('lo/')))


def decode_link(cfrom, cto):
    if cfrom == cto == None:
        return None
    elif None in (cfrom, cto):
        raise ValueError('Both cfrom and cto, or neither, must be specified.')
    else:
        return mrs.Link((int(cfrom), int(cto)), mrs.Link.CHARSPAN)

##############################################################################
##############################################################################
### Encoding

def encode(m):
    attributes = {}
    if m.link is not None and m.link.type == 'charspan':
        attributes['cfrom'] = str(sm.link.data[0])
        attributes['cto'] = str(sm.link.data[1])
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    e = etree.Element('mrs', attrib=attributes)
    listed_vars = set()
    e.append(encode_label(m.ltop))
    e.append(encode_index(m.index, listed_vars))
    for ep in m.rels:
        e.append(encode_ep(ep, listed_vars))
    for hcon in m.hcons:
        e.append(encode_hcon(hcon))
    return etree.tostring(e)

def encode_label(label):
    return etree.Element('label', vid=str(mrs.sort_vid_split(label)[1]))

def encode_handle(h):
    sort, vid = mrs.sort_vid_split(h)
    return etree.Element('var', vid=str(vid), sort=sort)

def encode_index(index, listed_vars):
    return encode_variable(index, listed_vars)

def encode_variable(v, listed_vars):
    var = etree.Element('var', vid=str(v.vid), sort=v.sort)
    if v.name not in listed_vars:
        var.extend(encode_extrapair(key, val) for key, val in v.props.items())
        listed_vars.add(v.name)
    return var

def encode_extrapair(key, value):
    extrapair = etree.Element('extrapair')
    path = etree.Element('path')
    path.text = key
    val = etree.Element('value')
    val.text = value
    extrapair.extend([path, val])
    return extrapair

def encode_ep(ep, listed_vars):
    attributes = {}
    if ep.link is not None and ep.link.type == 'charspan':
        attributes['cfrom'] = str(ep.link.data[0])
        attributes['cto'] = str(ep.link.data[1])
    if ep.surface is not None:
        attributes['surface'] = ep.surface
    if ep.base is not None:
        attributes['base'] = ep.base
    e = etree.Element('ep', attrib=attributes)
    e.append(encode_pred(ep.pred))
    e.append(encode_label(ep.label))
    for scargkey, scargval in ep.scargs.items():
        e.append(encode_scarg(scargkey, scargval))
    for argkey, argval in ep.args.items():
        e.append(encode_arg(argkey, argval, listed_vars))
    return e

def encode_pred(pred):
    p = None
    if pred.type == mrs.Pred.GPRED:
        p = etree.Element('pred')
        p.text = pred.string
    elif pred.type == mrs.Pred.SPRED:
        p = etree.Element('spred')
        p.text = pred.string
    elif pred.type == mrs.Pred.REALPRED:
        attributes = {'lemma': pred.lemma, 'pos': pred.pos}
        if pred.sense is not None:
            attributes['sense'] = pred.sense
        p = etree.Element('realpred', attrib=attributes)
    return p

def encode_scarg(key, value):
    fvpair = etree.Element('fvpair')
    rargname = etree.Element('rargname')
    rargname.text = key
    fvpair.append(rargname)
    fvpair.append(encode_handle(value))
    return fvpair

def encode_arg(key, value, listed_vars):
    fvpair = etree.Element('fvpair')
    rargname = etree.Element('rargname')
    rargname.text = key
    fvpair.append(rargname)
    if isinstance(value, str):
        const = etree.Element('constant')
        const.text = value
        fvpair.append(const)
    else:
        fvpair.append(encode_variable(value, listed_vars))
    return fvpair

def encode_hcon(hcon):
    hcons = etree.Element('hcons', hreln=hcon.relation)
    hi = etree.Element('hi')
    hi.append(encode_handle(hcon.lhandle))
    lo = etree.Element('lo')
    lo.append(encode_handle(hcon.rhandle))
    hcons.extend([hi, lo])
    return hcons
