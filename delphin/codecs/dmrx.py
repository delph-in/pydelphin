# -*- coding: utf-8 -*-

"""
DMRX (XML for DMRS) serialization and deserialization.
"""

from pathlib import Path
import xml.etree.ElementTree as etree

from delphin import predicate
from delphin.dmrs import (DMRS, Node, Link, CVARSORT)
from delphin.lnk import Lnk


CODEC_INFO = {
    'representation': 'dmrs',
}

HEADER = '<dmrs-list>'
JOINER = ''
FOOTER = '</dmrs-list>'


##############################################################################
##############################################################################
# Pickle-API methods


def load(source):
    """
    Deserialize DMRX from a file (handle or filename)

    Args:
        source (str, file): input filename or file object
    Returns:
        a list of DMRS objects
    """
    if not hasattr(source, 'read'):
        source = str(Path(source).expanduser())
    ms = _decode(source)
    return list(ms)


def loads(s):
    """
    Deserialize DMRX string representations

    Args:
        s (str): a DMRX string
    Returns:
        a list of DMRS objects
    """
    corpus = etree.fromstring(s)
    ds = (_decode_dmrs(dmrs_elem) for dmrs_elem in corpus)
    return list(ds)


def dump(ds, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize DMRS objects to DMRX and write to a file

    Args:
        ds: an iterator of DMRS objects to serialize
        destination: filename or file object where data will be written
        properties: if `False`, suppress morphosemantic properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    text = dumps(ds,
                 properties=properties,
                 lnk=lnk,
                 indent=indent)

    if hasattr(destination, 'write'):
        print(text, file=destination)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            print(text, file=fh)


def dumps(ds, properties=True, lnk=True, indent=False):
    """
    Serialize DMRS objects to a DMRX representation

    Args:
        ds: an iterator of DMRS objects to serialize
        properties: if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a DMRX string representation of a corpus of DMRS objects
    """
    return _encode(ds, properties, lnk, indent)


def decode(s):
    """
    Deserialize a DMRS object from a DMRX string.

    Note:
        This does not expect the top-level <dmrs-list> element.
    """
    elem = etree.fromstring(s)
    return _decode_dmrs(elem)


def encode(d, properties=True, lnk=True, indent=False):
    """
    Serialize a DMRS object to a DMRX string.

    Note:
        This does not include the top-level <dmrs-list> element, so it
        is not valid with the DMRX schema, but it may be more useful
        if you work with single DMRX objects at a time rather than
        lists of them.
    Args:
        d: a DMRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a DMRX-serialization of the DMRS object
    """
    elem = _encode_dmrs(d, properties, lnk)

    if indent is True or indent in ('LKB', 'Lkb', 'lkb'):
        _indent(elem, indent=0, maxdepth=2, level=0)
    elif indent is not False and indent is not None:
        _indent(elem, indent, maxdepth=3, level=0)

    s = etree.tostring(elem, encoding='unicode').rstrip()
    return s


##############################################################################
##############################################################################
# Decoding

def _decode(fh):
    # <!ELEMENT dmrs-list (dmrs)*>
    # if memory becomes a big problem, consider catching start events,
    # get the root element (later start events can be ignored), and
    # root.clear() after decoding each mrs
    for _, elem in etree.iterparse(fh, events=('end',)):
        if elem.tag == 'dmrs':
            yield _decode_dmrs(elem)
            elem.clear()


def _decode_dmrs(elem):
    # <!ELEMENT dmrs (node|link)*>
    # <!ATTLIST dmrs
    #           cfrom CDATA #REQUIRED
    #           cto   CDATA #REQUIRED
    #           surface   CDATA #IMPLIED
    #           ident     CDATA #IMPLIED >
    elem = elem.find('.')  # in case elem is an ElementTree rather than Element
    return DMRS(top=elem.get('top'),
                index=elem.get('index'),
                nodes=list(map(_decode_node, elem.iter('node'))),
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
    sortinfo = _decode_sortinfo(elem.find('sortinfo'))
    type = None
    if CVARSORT in sortinfo:
        type = sortinfo.pop(CVARSORT)
    return Node(id=int(elem.get('nodeid')),
                predicate=_decode_pred(elem.find('*[1]')),
                type=type,
                properties=sortinfo,  # without cvarsort; see above
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
        return elem.text
    elif elem.tag == 'realpred':
        return predicate.create(elem.get('lemma'),
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
    return Link(start=int(elem.get('from')),
                end=int(elem.get('to')),
                role=getattr(elem.find('rargname'), 'text', None),
                post=getattr(elem.find('post'), 'text', None))


def _decode_lnk(elem):
    return Lnk.charspan(elem.get('cfrom', '-1'), elem.get('cto', '-1'))

##############################################################################
##############################################################################
# Encoding


def _encode(ds, properties, lnk, indent):
    e = etree.Element('dmrs-list')
    for d in ds:
        e.append(_encode_dmrs(d, properties, lnk))

    if indent is True or indent in ('LKB', 'Lkb', 'lkb'):
        _indent(e, indent=0, maxdepth=3, level=0)
    elif indent is not False and indent is not None:
        _indent(e, indent, maxdepth=4, level=0)

    return etree.tostring(e, encoding='unicode').rstrip()


def _encode_dmrs(d, properties, lnk):
    attributes = {}
    if lnk:
        attributes['cfrom'] = str(d.cfrom)
        attributes['cto'] = str(d.cto)
    if d.top is not None:
        attributes['top'] = str(d.top)
    if d.index is not None:
        attributes['index'] = str(d.index)
    if lnk and d.surface is not None:
        attributes['surface'] = d.surface
    if d.identifier is not None:
        attributes['ident'] = d.identifier
    e = etree.Element('dmrs', attrib=attributes)
    for node in d.nodes:
        e.append(_encode_node(node, properties, lnk))
    for link in d.links:
        e.append(_encode_link(link))
    return e


def _encode_node(node, properties, lnk):
    attributes = {'nodeid': str(node.id)}
    if lnk:
        attributes['cfrom'] = str(node.cfrom)
        attributes['cto'] = str(node.cto)
        if node.surface is not None:
            attributes['surface'] = node.surface
        if node.base is not None:
            attributes['base'] = node.base
    if node.carg is not None:
        attributes['carg'] = node.carg
    e = etree.Element('node', attrib=attributes)
    e.append(_encode_pred(node.predicate))
    e.append(etree.Element('sortinfo',
                           attrib=node.sortinfo if properties else {}))
    return e


def _encode_pred(pred):
    if predicate.is_surface(pred):
        lemma, pos, sense = predicate.split(pred)
        attributes = {'lemma': lemma, 'pos': pos}
        if sense:
            attributes['sense'] = sense
        e = etree.Element('realpred', attrib=attributes)
    else:
        e = etree.Element('gpred')
        e.text = pred
    return e


def _encode_link(link):
    e = etree.Element('link',
                      attrib={'from': str(link.start),
                              'to': str(link.end)})
    rargname = etree.Element('rargname')
    rargname.text = link.role
    post = etree.Element('post')
    post.text = link.post
    e.append(rargname)
    e.append(post)
    return e


# inspired by Fredrik Lundh's indent() function:
#   http://effbot.org/zone/element-lib.htm
def _indent(elem, indent, maxdepth, level):
    if level == maxdepth:
        return
    curind = '\n' + ' ' * indent * level
    nxtind = '\n' + ' ' * indent * (level + 1)
    if len(elem):
        if not elem.text and level + 1 < maxdepth:
            elem.text = nxtind
        elem.tail = curind
        for elem in elem:
            _indent(elem, indent, maxdepth, level + 1)
        if level + 1 < maxdepth:
            elem.tail = curind
        else:
            elem.tail = ''
    else:
        elem.tail = curind
