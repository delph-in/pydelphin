# -*- coding: utf-8 -*-

"""
MRX (XML for MRS) serialization and deserialization.
"""

import io
import re
from pathlib import Path
import xml.etree.ElementTree as etree

from delphin.mrs import MRS, EP, HCons, ICons, CONSTANT_ROLE
from delphin import predicate
from delphin.lnk import Lnk
from delphin import variable
from delphin.sembase import role_priority, property_priority


CODEC_INFO = {
    'representation': 'mrs',
}

HEADER = '<mrs-list>'
JOINER = ''
FOOTER = '</mrs-list>'


##############################################################################
##############################################################################
# Pickle-API methods

def load(source):
    """
    Deserialize MRX from a file (handle or filename)

    Args:
        source (str, file): input filename or file object
    Returns:
        a list of MRS objects
    """
    if hasattr(source, 'read'):
        ms = list(_decode(source))
    else:
        source = Path(source).expanduser()
        with source.open() as fh:
            ms = list(_decode(fh))
    return ms


def loads(s):
    """
    Deserialize MRX string representations

    Args:
        s (str): an MRX string
    Returns:
        a list of MRS objects
    """
    ms = list(_decode(io.StringIO(s)))
    return ms


def dump(ms, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize MRS objects to MRX and write to a file

    Args:
        ms: an iterator of MRS objects to serialize
        destination: filename or file object where data will be written
        properties: if `False`, suppress morphosemantic properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ms, properties=properties, lnk=lnk, indent=indent)
    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ms, properties=True, lnk=True, indent=False):
    """
    Serialize MRS objects to an MRX representation

    Args:
        ms: an iterator of MRS objects to serialize
        properties: if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        an MRX string representation of a corpus of MRS objects
    """
    e = _encode(ms, properties, lnk)
    string = _tostring(e, indent, 1)
    return string


def decode(s):
    """
    Deserialize an MRS object from an MRX string.
    """
    elem = etree.fromstring(s)
    return _decode_mrs(elem)


def encode(m, properties=True, lnk=True, indent=False):
    """
    Serialize a MRS object to an MRX string.

    Args:
        m: an MRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        an MRX-serialization of the MRS object
    """
    e = _encode_mrs(m, properties, lnk)
    string = _tostring(e, indent, 0)
    return string


##############################################################################
##############################################################################
# Decoding


def _decode(fh):
    # <!ELEMENT mrs-list (mrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for _, elem in etree.iterparse(fh, events=('end',)):
        if elem.tag == 'mrs':
            yield _decode_mrs(elem)
            elem.clear()


def _decode_mrs(elem):
    # <!ELEMENT mrs (label, var, (ep|hcons)*)>
    # <!ATTLIST mrs
    #           cfrom     CDATA #IMPLIED
    #           cto       CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.')  # in case elem is ElementTree rather than Element
    variables = {}
    top = elem.find('label')
    if top is not None:
        top = _decode_label(top)
    index = elem.find('var')
    if index is not None:
        index = _decode_var(index, variables=variables)
    rels = [_decode_ep(ep, variables) for ep in elem.iter('ep')]
    hcons = [_decode_hcons(hc, variables) for hc in elem.iter('hcons')]
    icons = [_decode_icons(ic, variables) for ic in elem.iter('icons')]
    return MRS(top,
               index,
               rels,
               hcons,
               icons=icons,
               variables=variables,
               lnk=_decode_lnk(elem.get('cfrom'), elem.get('cto')),
               surface=elem.get('surface'),
               identifier=elem.get('ident'))


def _decode_label(elem):
    # <!ELEMENT label (extrapair*)>
    # <!ATTLIST label
    #           vid CDATA #REQUIRED >
    vid = elem.get('vid')
    # ignoring extrapairs
    return 'h' + vid


def _decode_var(elem, variables):
    # <!ELEMENT var (extrapair*)>
    # <!ATTLIST var
    #           vid  CDATA #REQUIRED
    #           sort (x|e|h|u|l|i) #IMPLIED >
    vid = elem.get('vid')
    srt = elem.get('sort').lower()
    var = srt + vid
    varprops = variables.setdefault(var, {})
    for prop, val in _decode_extrapairs(elem.iter('extrapair')):
        varprops[prop] = val
    return var


def _decode_extrapairs(elems):
    # <!ELEMENT extrapair (path,value)>
    # <!ELEMENT path (#PCDATA)>
    # <!ELEMENT value (#PCDATA)>
    return [(e.find('path').text.upper(), e.find('value').text.lower())
            for e in elems]


def _decode_ep(elem, variables=None):
    # <!ELEMENT ep ((pred|spred|realpred), label, fvpair*)>
    # <!ATTLIST ep
    #           cfrom CDATA #IMPLIED
    #           cto   CDATA #IMPLIED
    #           surface   CDATA #IMPLIED
    #           base      CDATA #IMPLIED >
    args = _decode_args(elem, variables=variables)
    return EP(_decode_pred(elem.find('./')),
              _decode_label(elem.find('label')),
              args=args,
              lnk=_decode_lnk(elem.get('cfrom'), elem.get('cto')),
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
    if elem.tag in ('pred', 'spred'):
        return elem.text
    elif elem.tag == 'realpred':
        return predicate.create(elem.get('lemma'),
                                elem.get('pos'),
                                elem.get('sense'))


def _decode_args(elem, variables=None):
    # <!ELEMENT fvpair (rargname, (var|constant))>
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


def _decode_hcons(elem, variables):
    # <!ELEMENT hcons (hi, lo)>
    # <!ATTLIST hcons
    #           hreln (qeq|lheq|outscopes) #REQUIRED >
    # <!ELEMENT hi (var)>
    # <!ELEMENT lo (label|var)>
    hi = _decode_var(elem.find('hi/var'), variables)
    lo = elem.find('lo/')
    if lo.tag == 'var':
        lo = _decode_var(lo, variables)
    else:
        lo = _decode_label(lo)
    return HCons(hi, elem.get('hreln'), lo)


# this isn't part of the spec; just putting here in case it's added later
def _decode_icons(elem, variables):
    # <!ELEMENT icons (left, right)>
    # <!ATTLIST icons
    #           ireln #REQUIRED >
    # <!ELEMENT left (var)>
    # <!ELEMENT right (var)>
    return ICons(_decode_var(elem.find('left/var'), variables),
                 elem.get('ireln'),
                 _decode_var(elem.find('right/var'), variables))


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


def _encode(ms, properties, lnk):
    e = etree.Element('mrs-list')
    for m in ms:
        e.append(_encode_mrs(m, properties, lnk))
    return e


def _encode_mrs(m, properties, lnk):
    if properties:
        varprops = dict(m.variables)
    else:
        varprops = {}
    attributes = {}
    if lnk:
        attributes['cfrom'] = str(m.cfrom)
        attributes['cto'] = str(m.cto)
        if m.surface is not None:
            attributes['surface'] = m.surface
    if m.identifier is not None:
        attributes['ident'] = m.identifier
    e = etree.Element('mrs', attrib=attributes)
    if m.top is not None:
        e.append(_encode_label(m.top))
    if m.index is not None:
        e.append(_encode_variable(m.index, varprops))
    for ep in m.rels:
        e.append(_encode_ep(ep, varprops, lnk))
    for hc in m.hcons:
        e.append(_encode_hcon(hc, varprops))
    for ic in m.icons:
        e.append(_encode_icon(ic, varprops))
    return e


def _encode_label(label):
    _, vid = variable.split(label)
    return etree.Element('label', vid=vid)


def _encode_variable(v, varprops):
    srt, vid = variable.split(v)
    var = etree.Element('var', vid=vid, sort=srt)
    if varprops.get(v):
        for key in sorted(varprops[v], key=property_priority):
            val = varprops[v][key]
            var.append(_encode_extrapair(key, val))
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


def _encode_ep(ep, varprops, lnk):
    attributes = {}
    if lnk:
        attributes['cfrom'] = str(ep.cfrom)
        attributes['cto'] = str(ep.cto)
        if ep.surface:
            attributes['surface'] = ep.surface
        if ep.base:
            attributes['base'] = ep.base
    e = etree.Element('ep', attrib=attributes)
    e.append(_encode_pred(ep.predicate))
    e.append(_encode_label(ep.label))
    for role in sorted(ep.args, key=role_priority):
        val = ep.args[role]
        if role == CONSTANT_ROLE:
            e.append(_encode_arg(CONSTANT_ROLE, _encode_constant(val)))
        else:
            e.append(_encode_arg(role, _encode_variable(val, varprops)))
    return e


def _encode_pred(pred):
    p = None
    if predicate.is_surface(pred):
        lemma, pos, sense = predicate.split(pred)
        attributes = {'lemma': lemma, 'pos': pos}
        if sense is not None:
            attributes['sense'] = sense
        p = etree.Element('realpred', attrib=attributes)
    elif predicate.is_abstract(pred):
        p = etree.Element('pred')
        p.text = pred
    else:
        p = etree.Element('spred')
        p.text = pred
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


def _encode_hcon(hcon, varprops):
    hcons_ = etree.Element('hcons', hreln=hcon.relation)
    hi = etree.Element('hi')
    hi.append(_encode_variable(hcon.hi, varprops))
    lo = etree.Element('lo')
    lo.append(_encode_label(hcon.lo))
    hcons_.extend([hi, lo])
    return hcons_


def _encode_icon(icon, varprops):
    icons_ = etree.Element('icons', ireln=icon.relation)
    left = etree.Element('left')
    left.append(_encode_variable(icon.left, varprops))
    right = etree.Element('right')
    right.append(_encode_variable(icon.right, varprops))
    icons_.extend([left, right])
    return icons_


def _tostring(e, indent, offset):
    string = etree.tostring(e, encoding='unicode')
    if indent is not None and indent is not False:
        if indent is True:
            indent = 0

        def indentmatch(m):
            return '\n' + (' ' * indent * (m.lastindex + offset)) + m.group()

        string = re.sub(
            r'(</mrs-list>)'
            r'|(<mrs[^-]|</mrs>)'
            r'|(<ep[>\s]|<fvpair>|<extrapair>|<hcons\s|<icons\s>)',
            indentmatch,
            string)

    return string.strip()
