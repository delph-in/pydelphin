
"""
MRX (XML for MRS) serialization and deserialization.
"""

# Author: Michael Wayne Goodman <goodmami@uw.edu>

from __future__ import print_function

from collections import defaultdict
import xml.etree.ElementTree as etree

from delphin.mrs import Mrs
from delphin.mrs.components import (
    ElementaryPredication, Pred, Lnk, HandleConstraint, IndividualConstraint,
    elementarypredications, hcons, icons, sort_vid_split, var_re
)
from delphin.exceptions import XmrsDeserializationError as XDE
from delphin.mrs.config import IVARG_ROLE
from delphin.mrs.util import etree_tostring


##############################################################################
##############################################################################
# Pickle-API methods


def load(fh, single=False):
    """
    Deserialize MRX from a file (handle or filename)

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
    Deserialize MRX string representations

    Args:
        s (str): a MRX string
        single (bool): if `True`, only return the first Xmrs object
    Returns:
        a generator of Xmrs objects (unless *single* is `True`)
    """
    corpus = etree.fromstring(s)
    if single:
        ds = _deserialize_mrs(next(corpus))
    else:
        ds = (_deserialize_mrs(mrs_elem) for mrs_elem in corpus)
    return ds


def dump(destination, ms, single=False, properties=True,
         encoding='unicode', pretty_print=False, **kwargs):
    """
    Serialize Xmrs objects to MRX and write to a file

    Args:
        destination: filename or file object where data will be written
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object
            instead of as an iterator
        properties: if `False`, suppress variable properties
        encoding: the character encoding of the string prior
            writing to a file (generally `"unicode"` is desired)
        pretty_print: if `True`, add newlines and indentation
    """
    text = dumps(ms,
                 single=single,
                 properties=properties,
                 encoding=encoding,
                 pretty_print=pretty_print,
                 **kwargs)

    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        with open(destination, 'w') as fh:
            print(text, file=fh)


def dumps(ms, single=False, properties=True,
          encoding='unicode', pretty_print=False, **kwargs):
    """
    Serialize an Xmrs object to a MRX representation

    Args:
        ms: an iterator of Xmrs objects to serialize (unless the
            *single* option is `True`)
        single: if `True`, treat *ms* as a single Xmrs object instead
            of as an iterator
        properties: if `False`, suppress variable properties
        encoding: the character encoding of the string (`"unicode"`
            returns a regular (unicode) string in Python 3 and a
            unicode string in Python 2)
        pretty_print: if `True`, add newlines and indentation
    Returns:
        a MRX string representation of a corpus of Xmrs
    """
    if not pretty_print and kwargs.get('indent'):
        pretty_print = True
    if single:
        ms = [ms]
    return serialize(ms, properties=properties,
                     encoding=encoding, pretty_print=pretty_print)

# for convenience

load_one = lambda fh: load(fh, single=True)
loads_one = lambda s: loads(s, single=True)
dump_one = lambda fh, m, **kwargs: dump(fh, m, single=True, **kwargs)
dumps_one = lambda m, **kwargs: dumps(m, single=True, **kwargs)

##############################################################################
##############################################################################
# Decoding


def deserialize(fh):
    # <!ELEMENT mrs-list (mrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for _, elem in etree.iterparse(fh, events=('end',)):
        if elem.tag == 'mrs':
            yield _deserialize_mrs(elem)
            elem.clear()


def _deserialize_mrs(elem):
    # <!ELEMENT mrs (label, var, (ep|hcons)*)>
    # <!ATTLIST mrs
    #           cfrom     CDATA #IMPLIED
    #           cto       CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.')  # in case elem is ElementTree rather than Element
    variables = defaultdict(list)
    # normalize_vars(elem) # try to make all vars have a sort
    top = elem.find('label')
    if top is not None:
        top = _decode_label(top)
    index = elem.find('var')
    if index is not None:
        index = _decode_var(index, variables=variables)
    return Mrs(top=top,
               index=index,
               rels=[_decode_ep(ep, variables) for ep in elem.iter('ep')],
               hcons=list(map(_decode_hcons, elem.iter('hcons'))),
               icons=list(map(_decode_icons, elem.iter('icons'))), # future
               lnk=_decode_lnk(elem.get('cfrom'), elem.get('cto')),
               surface=elem.get('surface'),
               identifier=elem.get('ident'),
               vars=variables)


def _decode_label(elem):
    # <!ELEMENT label (extrapair*)>
    # <!ATTLIST label
    #           vid CDATA #REQUIRED >
    return _decode_var(elem, sort='h')


def _decode_var(elem, sort=None, variables=None):
    # <!ELEMENT var (extrapair*)>
    # <!ATTLIST var
    #           vid  CDATA #REQUIRED
    #           sort (x|e|h|u|l|i) #IMPLIED >
    if variables is None: variables = defaultdict(list)
    vid = elem.get('vid')
    srt = sort or elem.get('sort')
    var = '%s%s' % (srt, str(vid))
    props = _decode_extrapairs(elem.iter('extrapair'))
    variables[var].extend(props)
    return var


def _decode_extrapairs(elems):
    # <!ELEMENT extrapair (path,value)>
    # <!ELEMENT path (#PCDATA)>
    # <!ELEMENT value (#PCDATA)>
    return [(e.find('path').text.upper(), e.find('value').text) for e in elems]


def _decode_ep(elem, variables=None):
    # <!ELEMENT ep ((pred|spred|realpred), label, fvpair*)>
    # <!ATTLIST ep
    #           cfrom CDATA #IMPLIED
    #           cto   CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED >
    return ElementaryPredication(None,  # no nodeid in MRS
                                 _decode_pred(elem.find('./')),
                                 _decode_label(elem.find('label')),
                                 args=_decode_args(elem, variables=variables),
                                 lnk=_decode_lnk(elem.get('cfrom'),
                                                elem.get('cto')),
                                 surface=elem.get('surface'),
                                 base=elem.get('base'))


def _decode_pred(elem):
    # <!ELEMENT pred (#PCDATA)>
    # <!ELEMENT spred (#PCDATA)>
    # <!ELEMENT realpred EMPTY>
    # <!ATTLIST realpred
    #           lemma CDATA #REQUIRED
    #           pos (v|n|j|r|p|q|c|x|u|a|s) #REQUIRED
    #           sense CDATA #IMPLIED >
    if elem.tag == 'pred':
        return Pred.abstract(elem.text)
    elif elem.tag == 'spred':
        return Pred.surface(elem.text)
    elif elem.tag == 'realpred':
        return Pred.realpred(elem.get('lemma'),
                             elem.get('pos') or None,
                             elem.get('sense'))


def _decode_args(elem, variables=None):
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
            argval = _decode_var(e.find('var'), variables=variables)
        args[rargname] = argval
    return args


def _decode_hcons(elem):
    # <!ELEMENT hcons (hi, lo)>
    # <!ATTLIST hcons
    #           hreln (qeq|lheq|outscopes) #REQUIRED >
    # <!ELEMENT hi (var)>
    # <!ELEMENT lo (label|var)>
    lo = elem.find('lo/')
    return HandleConstraint(_decode_var(elem.find('hi/var')),
                            elem.get('hreln'),
                            _decode_var(lo) if lo.tag == 'var' else
                            _decode_label(lo))


# this isn't part of the spec; just putting here in case it's added later
def _decode_icons(elem):
    # <!ELEMENT icons (left, right)>
    # <!ATTLIST icons
    #           ireln #REQUIRED >
    # <!ELEMENT left (var)>
    # <!ELEMENT right (var)>
    return IndividualConstraint(_decode_var(elem.find('left/var')),
                                elem.get('ireln'),
                                _decode_var(elem.find('right/var')))


def _decode_lnk(cfrom, cto):
    if cfrom is cto is None:
        return None
    elif None in (cfrom, cto):
        raise ValueError('Both cfrom and cto, or neither, must be specified.')
    else:
        return Lnk.charspan(cfrom, cto)

##############################################################################
##############################################################################
# Encoding


def serialize(ms, properties=True, encoding='unicode', pretty_print=False):
    e = etree.Element('mrs-list')
    for m in ms:
        e.append(_encode_mrs(m, properties))
    if pretty_print:
        import re
        pprint_re = re.compile(r'(<mrs[^-]|</mrs>|</mrs-list>'
                               r'|<ep\s|<fvpair>|<extrapair>|<hcons\s)',
                               re.IGNORECASE)
        string = etree_tostring(e, encoding=encoding)
        return pprint_re.sub(r'\n\1', string)
    return etree_tostring(e, encoding=encoding)


def _encode_mrs(m, properties):
    if properties:
        varprops = {v: d['props'] for v, d in m._vars.items() if d['props']}
    else:
        varprops = {}
    attributes = {'cfrom': str(m.cfrom), 'cto': str(m.cto)}
    if m.surface is not None:
        attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    e = etree.Element('mrs', attrib=attributes)
    if m.top is not None:
        e.append(_encode_label(m.top))
    if m.index is not None:
        e.append(_encode_variable(m.index, varprops))
    for ep in elementarypredications(m):
        e.append(_encode_ep(ep, varprops))
    for hcon in hcons(m):
        e.append(_encode_hcon(hcon))
    for icon in icons(m):
        e.append(_encode_icon(icon))
    return e


def _encode_label(label):
    _, vid = sort_vid_split(label)
    return etree.Element('label', vid=vid)


def _encode_variable(v, varprops=None):
    if varprops is None: varprops = {}
    srt, vid = sort_vid_split(v)
    var = etree.Element('var', vid=vid, sort=srt)
    if v in varprops:
        var.extend(_encode_extrapair(key, val)
                   for key, val in varprops[v])
        del varprops[v]
    return var


def _encode_extrapair(key, value):
    extrapair = etree.Element('extrapair')
    path = etree.Element('path')
    path.text = key
    val = etree.Element('value')
    val.text = value
    extrapair.extend([path, val])
    return extrapair


def _encode_ep(ep, varprops=None):
    attributes = {'cfrom': str(ep.cfrom), 'cto': str(ep.cto)}
    if ep.surface is not None:
        attributes['surface'] = ep.surface
    if ep.base is not None:
        attributes['base'] = ep.base
    e = etree.Element('ep', attrib=attributes)
    e.append(_encode_pred(ep.pred))
    e.append(_encode_label(ep.label))
    for rargname, val in ep.args.items():
        if var_re.match(val):
            e.append(_encode_arg(rargname, _encode_variable(val, varprops)))
        else:
            e.append(_encode_arg(rargname, _encode_constant(val)))
    return e


def _encode_pred(pred):
    p = None
    if pred.type == Pred.ABSTRACT:
        p = etree.Element('pred')
        p.text = pred.string
    elif pred.type == Pred.SURFACE:
        p = etree.Element('spred')
        p.text = pred.string
    elif pred.type == Pred.REALPRED:
        attributes = {'lemma': pred.lemma, 'pos': pred.pos or ""}
        if pred.sense is not None:
            attributes['sense'] = pred.sense
        p = etree.Element('realpred', attrib=attributes)
    return p


def _encode_arg(key, value):
    fvpair = etree.Element('fvpair')
    rargname = etree.Element('rargname')
    rargname.text = key
    fvpair.append(rargname)
    fvpair.append(value)
    return fvpair


def _encode_constant(value):
    const = etree.Element('constant')
    const.text = value
    return const


def _encode_hcon(hcon):
    hcons_ = etree.Element('hcons', hreln=hcon.relation)
    hi = etree.Element('hi')
    hi.append(_encode_variable(hcon.hi))
    lo = etree.Element('lo')
    lo.append(_encode_variable(hcon.lo))
    hcons_.extend([hi, lo])
    return hcons_

def _encode_icon(icon):
    icons_ = etree.Element('icons', ireln=icon.relation)
    left = etree.Element('left')
    left.append(_encode_variable(icon.left))
    right = etree.Element('right')
    right.append(_encode_variable(icon.right))
    icons_.extend([left, right])
    return icons_
