# -*- coding: utf-8 -*-

"""
MRS-JSON serialization and deserialization.

Example:

* *The new chef whose soup accidentally spilled quit and left.*

::

  {
    "top": "h0",
    "index": "e2",
    "relations": [
      {
        "label": "h4",
        "predicate": "_the_q",
        "lnk": {"from": 0, "to": 3},
        "arguments": {"BODY": "h6", "RSTR": "h5", "ARG0": "x3"}
      },
      {
        "label": "h7",
        "predicate": "_new_a_1",
        "lnk": {"from": 4, "to": 7},
        "arguments": {"ARG1": "x3", "ARG0": "e8"}
      },
      {
        "label": "h7",
        "predicate": "_chef_n_1",
        "lnk": {"from": 8, "to": 12},
        "arguments": {"ARG0": "x3"}
      },
      {
        "label": "h9",
        "predicate": "def_explicit_q",
        "lnk": {"from": 13, "to": 18},
        "arguments": {"BODY": "h12", "RSTR": "h11", "ARG0": "x10"}
      },
      {
        "label": "h13",
        "predicate": "poss",
        "lnk": {"from": 13, "to": 18},
        "arguments": {"ARG1": "x10", "ARG2": "x3", "ARG0": "e14"}
      },
      {
        "label": "h13",
        "predicate": "_soup_n_1",
        "lnk": {"from": 19, "to": 23},
        "arguments": {"ARG0": "x10"}
      },
      {
        "label": "h7",
        "predicate": "_accidental_a_1",
        "lnk": {"from": 24, "to": 36},
        "arguments": {"ARG1": "e16", "ARG0": "e15"}
      },
      {
        "label": "h7",
        "predicate": "_spill_v_1",
        "lnk": {"from": 37, "to": 44},
        "arguments": {"ARG1": "x10", "ARG2": "i17", "ARG0": "e16"}
      },
      {
        "label": "h1",
        "predicate": "_quit_v_1",
        "lnk": {"from": 45, "to": 49},
        "arguments": {"ARG1": "x3", "ARG2": "i19", "ARG0": "e18"}
      },
      {
        "label": "h1",
        "predicate": "_and_c",
        "lnk": {"from": 50, "to": 53},
        "arguments": {"ARG1": "e18", "ARG2": "e20", "ARG0": "e2"}
      },
      {
        "label": "h1",
        "predicate": "_leave_v_1",
        "lnk": {"from": 54, "to": 59},
        "arguments": {"ARG1": "x3", "ARG2": "i21", "ARG0": "e20"}
      }
    ],
    "constraints": [
      {"low": "h1", "high": "h0", "relation": "qeq"},
      {"low": "h7", "high": "h5", "relation": "qeq"},
      {"low": "h13", "high": "h11", "relation": "qeq"}
    ],
    "variables": {
      "h0": {"type": "h"},
      "h1": {"type": "h"},
      "e2": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "-", "SF": "prop", "PERF": "-", "TENSE": "past"}},
      "x3": {"type": "x", "properties": {"NUM": "sg", "PERS": "3", "IND": "+"}},
      "h4": {"type": "h"},
      "h6": {"type": "h"},
      "h5": {"type": "h"},
      "h7": {"type": "h"},
      "e8": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "bool", "SF": "prop", "PERF": "-", "TENSE": "untensed"}},
      "h9": {"type": "h"},
      "x10": {"type": "x", "properties": {"NUM": "sg", "PERS": "3"}},
      "h11": {"type": "h"},
      "h12": {"type": "h"},
      "h13": {"type": "h"},
      "e14": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "-", "SF": "prop", "PERF": "-", "TENSE": "untensed"}},
      "e15": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "-", "SF": "prop", "PERF": "-", "TENSE": "untensed"}},
      "e16": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "-", "SF": "prop", "PERF": "-", "TENSE": "past"}},
      "i17": {"type": "i"},
      "e18": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "-", "SF": "prop", "PERF": "-", "TENSE": "past"}},
      "i19": {"type": "i"},
      "e20": {"type": "e", "properties": {"MOOD": "indicative", "PROG": "-", "SF": "prop", "PERF": "-", "TENSE": "past"}},
      "i21": {"type": "i"}
    }
  }
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
    Decode a dictionary, as from `to_dict()`, into an MRS object.
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
