
# MRX codec
# Summary: This module implements serialization and deserialization of
#          the XML encoding of Minimal Recusion Semantics. It provides
#          standard Pickle API calls of load, loads, dump, and dumps for
#          serializing and deserializing single MRX instances.
#          Further, encode_list and decode_list are provided for lists
#          of MRX instances, and they read and write incrementally.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from . import (Mrs, MrsVariable, Pred, Lnk, ElementaryPredication,
               HandleConstraint)
from .mrserrors import MrsDecodeError
from collections import OrderedDict

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

def dump(fh, m, encoding='unicode', pretty_print=False):
    fh.write(dumps(m, encoding=encoding, pretty_print=pretty_print))

def dumps(m, encoding='unicode', pretty_print=False):
    return encode(m, encoding=encoding, pretty_print=pretty_print)

##############################################################################
##############################################################################
### Decoding

HANDLE_PREFIX = 'h'
_CV = 'ARG0' # characteristic variable
_CARG = 'CARG' # constant argument
_FIRST_NODEID = 10001

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
    #normalize_vars(elem) # try to make all vars have a sort
    return Mrs(ltop = decode_label(elem.find('label')),
               index = decode_var(elem.find('var')),
               rels = [decode_ep(ep, nodeid=_FIRST_NODEID + i)
                       for i, ep in enumerate(elem.iter('ep'))],
               hcons = [decode_hcons(h) for h in elem.iter('hcons')],
               lnk = decode_lnk(elem.get('cfrom'), elem.get('cto')),
               surface = elem.get('surface'),
               identifier = elem.get('ident'))

def decode_label(elem):
    # <!ELEMENT label (extrapair*)>
    # <!ATTLIST label
    #           vid CDATA #REQUIRED >
    return decode_var(elem, sort='h')

def decode_var(elem, sort=None):
    # <!ELEMENT var (extrapair*)>
    # <!ATTLIST var
    #           vid  CDATA #REQUIRED
    #           sort (x|e|h|u|l|i) #IMPLIED >
    return MrsVariable(vid=elem.get('vid'), sort=sort or elem.get('sort'),
                       properties=decode_extrapairs(elem.iter('extrapair')))

def decode_extrapairs(elems):
    # <!ELEMENT extrapair (path,value)>
    # <!ELEMENT path (#PCDATA)>
    # <!ELEMENT value (#PCDATA)>
    return OrderedDict((e.find('path').text.upper(), e.find('value').text)
                       for e in elems)

def decode_ep(elem, nodeid=0):
    # <!ELEMENT ep ((pred|spred|realpred), label, fvpair*)>
    # <!ATTLIST ep
    #           cfrom CDATA #IMPLIED
    #           cto   CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED >
    cv, args, carg = decode_args(elem)
    return ElementaryPredication(pred=decode_pred(elem.find('./')),
                                 nodeid=nodeid,
                                 label=decode_label(elem.find('label')),
                                 cv=cv,
                                 args=args,
                                 lnk=decode_lnk(elem.get('cfrom'),
                                                elem.get('cto')),
                                 surface=elem.get('surface'),
                                 base=elem.get('base'),
                                 carg=carg)

def decode_pred(elem):
    # <!ELEMENT pred (#PCDATA)>
    # <!ELEMENT spred (#PCDATA)>
    # <!ELEMENT realpred EMPTY>
    # <!ATTLIST realpred
    #           lemma CDATA #REQUIRED
    #           pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #           sense CDATA #IMPLIED >
    print(elem.text)
    if elem.tag in ('pred', 'spred'):
        return Pred(string=elem.text)
    elif elem.tag == 'realpred':
        return Pred(lemma=elem.get('lemma'),
                    pos=elem.get('pos'),
                    sense=elem.get('sense'))

def decode_args(elem):
    # <!ELEMENT fvpair (rargname, (var|constant))>
    # cv is the characteristic variable (probably ARG0, given by _CV)
    # carg is the constant arg (e.g. a quoted string; given by _CARG)
    # This code assumes that only cargs have constant values, and all
    # other args (including CVs) have var values.
    args = OrderedDict()
    cv = carg = None
    for e in elem.findall('fvpair'):
        argname = e.find('rargname').text.upper()
        if argname == _CV:
            cv = decode_var(e.find('var'))
        elif argname == _CARG:
            carg = e.find('constant').text
        else:
            args[argname] = decode_var(e.find('var'))
    return cv, args, carg

def decode_hcons(elem):
    # <!ELEMENT hcons (hi, lo)>
    # <!ATTLIST hcons
    #           hreln (qeq|lheq|outscopes) #REQUIRED >
    # <!ELEMENT hi (var)>
    # <!ELEMENT lo (label|var)>
    lo = elem.find('lo/')
    return HandleConstraint(decode_var(elem.find('hi/var')),
                            elem.get('hreln'),
                            decode_var(lo) if lo.tag == 'var' else
                            decode_label(lo))

def decode_lnk(cfrom, cto):
    if cfrom == cto == None:
        return None
    elif None in (cfrom, cto):
        raise ValueError('Both cfrom and cto, or neither, must be specified.')
    else:
        return Lnk((int(cfrom), int(cto)), Lnk.CHARSPAN)

##############################################################################
##############################################################################
### Encoding

def encode(m, encoding='unicode', pretty_print=False):
    attributes = {}
    if m.lnk is not None and m.lnk.type == Lnk.CHARSPAN:
        attributes['cfrom'] = str(m.lnk.data[0])
        attributes['cto'] = str(m.lnk.data[1])
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    e = etree.Element('mrs', attrib=attributes)
    listed_vars = set()
    e.append(encode_label(m.ltop))
    e.append(encode_variable(m.index, listed_vars))
    for ep in m.rels:
        e.append(encode_ep(ep, listed_vars))
    for hcon in m.hcons:
        e.append(encode_hcon(hcon))
    if pretty_print:
        import re
        pprint_re = re.compile(r'(<ep\s|<fvpair>|<extrapair>|<hcons\s|</mrs>)',
                               re.IGNORECASE)
        string = etree.tostring(e, encoding=encoding)
        return pprint_re.sub(r'\n\1', string)
    return etree.tostring(e, encoding=encoding)

def encode_label(label):
    return etree.Element('label', vid=str(label.vid))

def encode_variable(v, listed_vars=set()):
    var = etree.Element('var', vid=str(v.vid), sort=v.sort)
    if v.vid not in listed_vars and v.properties:
        var.extend(encode_extrapair(key, val)
                   for key, val in v.properties.items())
        listed_vars.add(v.vid)
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
    if ep.lnk is not None and ep.lnk.type == Lnk.CHARSPAN:
        attributes['cfrom'] = str(ep.lnk.data[0])
        attributes['cto'] = str(ep.lnk.data[1])
    if ep.surface is not None:
        attributes['surface'] = ep.surface
    if ep.base is not None:
        attributes['base'] = ep.base
    e = etree.Element('ep', attrib=attributes)
    e.append(encode_pred(ep.pred))
    e.append(encode_label(ep.label))
    if ep.cv is not None:
        e.append(encode_arg(_CV, encode_variable(ep.cv, listed_vars)))
    for argkey, argval in ep.args.items():
        e.append(encode_arg(argkey, encode_variable(argval, listed_vars)))
    if ep.carg is not None:
        e.append(encode_arg(_CARG, encode_constant(ep.carg)))
    return e

def encode_pred(pred):
    p = None
    if pred.type == Pred.GPRED:
        p = etree.Element('pred')
        p.text = pred.string
    elif pred.type == Pred.SPRED:
        p = etree.Element('spred')
        p.text = pred.string
    elif pred.type == Pred.REALPRED:
        attributes = {'lemma': pred.lemma, 'pos': pred.pos}
        if pred.sense is not None:
            attributes['sense'] = pred.sense
        p = etree.Element('realpred', attrib=attributes)
    return p

def encode_arg(key, value):
    fvpair = etree.Element('fvpair')
    rargname = etree.Element('rargname')
    rargname.text = key
    fvpair.append(rargname)
    fvpair.append(value)
    return fvpair

def encode_constant(value):
    const = etree.Element('constant')
    const.text = value
    return const

def encode_hcon(hcon):
    hcons = etree.Element('hcons', hreln=hcon.relation)
    hi = etree.Element('hi')
    hi.append(encode_variable(hcon.lhandle))
    lo = etree.Element('lo')
    lo.append(encode_variable(hcon.rhandle))
    hcons.extend([hi, lo])
    return hcons
