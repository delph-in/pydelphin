
# MRX codec
# Summary: This module implements serialization and deserialization of
#          the XML encoding of Minimal Recusion Semantics. It provides
#          standard Pickle API calls of load, loads, dump, and dumps for
#          serializing and deserializing single MRX instances.
#          Further, encode_list and decode_list are provided for lists
#          of MRX instances, and they read and write incrementally.
# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function

from collections import defaultdict
import xml.etree.ElementTree as etree

from delphin.mrs import Mrs
from delphin.mrs.components import (
    ElementaryPredication, Pred, Lnk, HandleConstraint,
    elementarypredications, hcons, icons, sort_vid_split, var_re
)
from delphin._exceptions import XmrsDeserializationError as XDE
from delphin.mrs.config import IVARG_ROLE
from delphin.mrs.util import etree_tostring


##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    ms = decode(fh)
    if single:
        ms = next(ms)
    return ms


def loads(s, single=False):
    corpus = etree.fromstring(s)
    if single:
        ds = decode_mrs(next(corpus))
    else:
        ds = (decode_mrs(mrs_elem) for mrs_elem in corpus)
    return ds


def dump(fh, ms, **kwargs):
    print(dumps(ms, **kwargs), file=fh)


def dumps(ms, single=False, encoding='unicode', pretty_print=False, **kwargs):
    if single:
        ms = [ms]
    return encode(ms, encoding=encoding, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding

# it's not ideal to have this here, but anyway make sure it is reset
# for each decoding. It's used to unify variables
_vars = {}


def decode(fh):
    """Decode an MRX-encoded MRS structure."""
    # <!ELEMENT mrs-list (mrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for event, elem in etree.iterparse(fh, events=('end',)):
        if elem.tag == 'mrs':
            yield decode_mrs(elem)
            elem.clear()


def decode_mrs(elem):
    # <!ELEMENT mrs (label, var, (ep|hcons)*)>
    # <!ATTLIST mrs
    #           cfrom     CDATA #IMPLIED
    #           cto       CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.')  # in case elem is ElementTree rather than Element
    variables = defaultdict(list)
    # normalize_vars(elem) # try to make all vars have a sort
    return Mrs(top=decode_label(elem.find('label')),
               index=decode_var(elem.find('var'), variables=variables),
               rels=[decode_ep(ep, variables) for ep in elem.iter('ep')],
               hcons=list(map(decode_hcons, elem.iter('hcons'))),
               icons=list(map(decode_icons, elem.iter('icons'))), # future
               lnk=decode_lnk(elem.get('cfrom'), elem.get('cto')),
               surface=elem.get('surface'),
               identifier=elem.get('ident'),
               vars=variables)


def decode_label(elem):
    # <!ELEMENT label (extrapair*)>
    # <!ATTLIST label
    #           vid CDATA #REQUIRED >
    return decode_var(elem, sort='h')


def decode_var(elem, sort=None, variables=None):
    # <!ELEMENT var (extrapair*)>
    # <!ATTLIST var
    #           vid  CDATA #REQUIRED
    #           sort (x|e|h|u|l|i) #IMPLIED >
    if variables is None: variables = defaultdict(list)
    vid = elem.get('vid')
    srt = sort or elem.get('sort')
    var = '%s%s' % (srt, str(vid))
    props = decode_extrapairs(elem.iter('extrapair'))
    variables[var].extend(props)
    return var


def decode_extrapairs(elems):
    # <!ELEMENT extrapair (path,value)>
    # <!ELEMENT path (#PCDATA)>
    # <!ELEMENT value (#PCDATA)>
    return [(e.find('path').text.upper(), e.find('value').text) for e in elems]


def decode_ep(elem, variables=None):
    # <!ELEMENT ep ((pred|spred|realpred), label, fvpair*)>
    # <!ATTLIST ep
    #           cfrom CDATA #IMPLIED
    #           cto   CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED >
    return ElementaryPredication(None,  # no nodeid in MRS
                                 decode_pred(elem.find('./')),
                                 decode_label(elem.find('label')),
                                 args=decode_args(elem, variables=variables),
                                 lnk=decode_lnk(elem.get('cfrom'),
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
    if elem.tag == 'pred':
        return Pred.grammarpred(elem.text)
    elif elem.tag == 'spred':
        return Pred.stringpred(elem.text)
    elif elem.tag == 'realpred':
        return Pred.readpred(elem.get('lemma'),
                             elem.get('pos'),
                             elem.get('sense'))


def decode_args(elem, variables=None):
    # <!ELEMENT fvpair (rargname, (var|constant))>
    # iv is the intrinsic variable (probably ARG0, given by IVARG_ROLE)
    # carg is the constant arg (e.g. a quoted string; given by CONSTARG_ROLE)
    # This code assumes that only cargs have constant values, and all
    # other args (including IVs) have var values.
    args = {}
    for e in elem.findall('fvpair'):
        rargname = e.find('rargname').text.upper()
        if e.find('constant') is not None:
            argval = e.find('constant').text
        elif e.find('var') is not None:
            argval = decode_var(e.find('var'), variables=variables)
        args[rargname] = argval
    return args


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


# this isn't part of the spec; just putting here in case it's added later
def decode_icons(elem):
    # <!ELEMENT icons (left, right)>
    # <!ATTLIST icons
    #           ireln #REQUIRED >
    # <!ELEMENT left (var)>
    # <!ELEMENT right (var)>
    return IndividualConstraint(decode_var(elem.find('left/var')),
                                elem.get('ireln'),
                                decode_var(elem.find('right/var')))


def decode_lnk(cfrom, cto):
    if cfrom is cto is None:
        return None
    elif None in (cfrom, cto):
        raise ValueError('Both cfrom and cto, or neither, must be specified.')
    else:
        return Lnk.charspan(cfrom, cto)

##############################################################################
##############################################################################
# Encoding


def encode(ms, encoding='unicode', pretty_print=False):
    e = etree.Element('mrs-list')
    for m in ms:
        e.append(encode_mrs(m))
    if pretty_print:
        import re
        pprint_re = re.compile(r'(<mrs[^-]|</mrs>|</mrs-list>'
                               r'|<ep\s|<fvpair>|<extrapair>|<hcons\s)',
                               re.IGNORECASE)
        string = etree_tostring(e, encoding=encoding)
        return pprint_re.sub(r'\n\1', string)
    return etree_tostring(e, encoding=encoding)


def encode_mrs(m):
    varprops = {v: vd['props'] for v, vd in m._vars.items() if vd['props']}
    attributes = {'cfrom': str(m.cfrom), 'cto': str(m.cto)}
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    e = etree.Element('mrs', attrib=attributes)
    if m.top is not None:
        e.append(encode_label(m.top))
    if m.index is not None:
        e.append(encode_variable(m.index, varprops))
    for ep in elementarypredications(m):
        e.append(encode_ep(ep, varprops))
    for hcon in hcons(m):
        e.append(encode_hcon(hcon))
    for icon in icons(m):
        e.append(encode_icon(icon))
    return e


def encode_label(label):
    srt, vid = sort_vid_split(label)
    return etree.Element('label', vid=vid)


def encode_variable(v, varprops=None):
    if varprops is None: varprops = {}
    srt, vid = sort_vid_split(v)
    var = etree.Element('var', vid=vid, sort=srt)
    if v in varprops:
        var.extend(encode_extrapair(key, val)
                   for key, val in varprops[v])
        del varprops[v]
    return var


def encode_extrapair(key, value):
    extrapair = etree.Element('extrapair')
    path = etree.Element('path')
    path.text = key
    val = etree.Element('value')
    val.text = value
    extrapair.extend([path, val])
    return extrapair


def encode_ep(ep, varprops=None):
    attributes = {'cfrom': str(ep.cfrom), 'cto': str(ep.cto)}
    if ep.surface is not None:
        attributes['surface'] = ep.surface
    if ep.base is not None:
        attributes['base'] = ep.base
    e = etree.Element('ep', attrib=attributes)
    e.append(encode_pred(ep.pred))
    e.append(encode_label(ep.label))
    if ep.iv is not None:
        e.append(encode_arg(IVARG_ROLE, encode_variable(ep.iv, varprops)))
    for rargname, val in ep.args.items():
        if var_re.match(val):
            e.append(encode_arg(rargname, encode_variable(val, varprops)))
        else:
            e.append(encode_arg(rargname, encode_constant(val)))
    return e


def encode_pred(pred):
    p = None
    if pred.type == Pred.GRAMMARPRED:
        p = etree.Element('pred')
        p.text = pred.string
    elif pred.type == Pred.STRINGPRED:
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
    hcons_ = etree.Element('hcons', hreln=hcon.relation)
    hi = etree.Element('hi')
    hi.append(encode_variable(hcon.hi))
    lo = etree.Element('lo')
    lo.append(encode_variable(hcon.lo))
    hcons_.extend([hi, lo])
    return hcons_

def encode_icon(icon):
    icons_ = etree.Element('icons', ireln=icon.relation)
    left = etree.Element('left')
    left.append(encode_variable(icon.left))
    right = etree.Element('right')
    right.append(encode_variable(icon.right))
    icons_.extend([left, right])
    return icons_
