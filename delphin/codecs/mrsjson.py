# -*- coding: utf-8 -*-

"""
MRS-JSON serialization and deserialization.
"""

from pathlib import Path
import json

from delphin.lnk import Lnk
from delphin import variable
from delphin.mrs import (MRS, EP, HCons, ICons)


CODEC_INFO = {
    'representation': 'mrs',
}

HEADER = '['
JOINER = ','
FOOTER = ']'


def load(source):
    """
    Deserialize a MRS-JSON file (handle or filename) to MRS objects

    Args:
        source: filename or file object
    Returns:
        a list of MRS objects
    """
    if hasattr(source, 'read'):
        data = json.load(source)
    else:
        source = Path(source).expanduser()
        with source.open() as fh:
            data = json.load(fh)
    return [from_dict(d) for d in data]


def loads(s):
    """
    Deserialize a MRS-JSON string to MRS objects

    Args:
        s (str): a MRS-JSON string
    Returns:
        a list of MRS objects
    """
    data = json.loads(s)
    return [from_dict(d) for d in data]


def dump(ms, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize MRS objects to a MRS-JSON file.

    Args:
        ms: iterator of :class:`~delphin.mrs.MRS` objects to
            serialize
        destination: filename or file object
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
        encoding (str): if *destination* is a filename, write to the
            file with the given encoding; otherwise it is ignored
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    data = [to_dict(m, properties=properties, lnk=lnk) for m in ms]
    if hasattr(destination, 'write'):
        json.dump(data, destination, indent=indent)
    else:
        destination = Path(destination).expanduser()
        with destination.open('w', encoding=encoding) as fh:
            json.dump(data, fh)


def dumps(ms, properties=True, lnk=True, indent=False):
    """
    Serialize MRS objects to a MRS-JSON string.

    Args:
        ms: iterator of :class:`~delphin.mrs.MRS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        a MRS-JSON-serialization of the MRS objects
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    data = [to_dict(m, properties=properties, lnk=lnk) for m in ms]
    return json.dumps(data, indent=indent)


def decode(s):
    """
    Deserialize a MRS object from a MRS-JSON string.
    """
    return from_dict(json.loads(s))


def encode(m, properties=True, lnk=True, indent=False):
    """
    Serialize a MRS object to a MRS-JSON string.

    Args:
        m: a MRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a MRS-JSON-serialization of the MRS object
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    return json.dumps(to_dict(m, properties=properties, lnk=lnk),
                      indent=indent)


def to_dict(mrs, properties=True, lnk=True):
    """
    Encode the MRS as a dictionary suitable for JSON serialization.
    """

    def _ep(ep):
        d = {'label': ep.label,
             'predicate': ep.predicate,
             'arguments': ep.args}
        if lnk:
            if ep.lnk:
                d['lnk'] = {'from': ep.cfrom, 'to': ep.cto}
            if ep.surface:
                d['surface'] = ep.surface
            if ep.base:
                d['base'] = ep.base
        return d

    def _hcons(hc):
        return {'relation': hc.relation, 'high': hc.hi, 'low': hc.lo}

    def _icons(ic):
        return {'relation': ic.relation, 'left': ic.left, 'right': ic.right}

    def _var(v):
        d = {'type': variable.type(v)}
        if properties and mrs.variables.get(v):
            d['properties'] = dict(mrs.variables[v])
        return d

    d = dict(
        top=mrs.top,
        index=mrs.index,
        relations=list(map(_ep, mrs.rels)),
        constraints=(list(map(_hcons, mrs.hcons))
                     + list(map(_icons, mrs.icons))),
        variables={v: _var(v) for v in mrs.variables})
    # if mrs.lnk is not None: d['lnk'] = mrs.lnk
    # if mrs.surface is not None: d['surface'] = mrs.surface
    # if mrs.identifier is not None: d['identifier'] = mrs.identifier
    return d


def from_dict(d):
    """
    Decode a dictionary, as from :func:`to_dict`, into an MRS object.
    """

    def _lnk(o):
        return None if o is None else Lnk.charspan(o['from'], o['to'])

    def _ep(_d):
        return EP(
            _d['predicate'],
            _d['label'],
            args=_d.get('arguments', {}),
            lnk=_lnk(_d.get('lnk')),
            surface=_d.get('surface'),
            base=_d.get('base'))

    def _hcons(_d):
        return HCons(_d['high'], _d['relation'], _d['low'])

    def _icons(_d):
        return ICons(_d['left'], _d['relation'], _d['right'])

    hcons = [c for c in d.get('constraints', []) if 'high' in c]
    icons = [c for c in d.get('constraints', []) if 'left' in c]
    variables = {var: data.get('properties', {})
                 for var, data in d.get('variables', {}).items()}

    return MRS(
        d['top'],
        d.get('index'),
        list(map(_ep, d.get('relations', []))),
        list(map(_hcons, hcons)),
        icons=list(map(_icons, icons)),
        variables=variables,
        lnk=_lnk(d.get('lnk')),
        surface=d.get('surface'),
        identifier=d.get('identifier')
    )
