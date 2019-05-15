# -*- coding: utf-8 -*-

"""
EDS-JSON serialization and deserialization.

Example:

* *The new chef whose soup accidentally spilled quit and left.*

::

  {
    "top": "e18",
    "nodes": {
      "_1": {
        "label": "_the_q",
        "lnk": {"from": 0, "to": 3},
        "edges": {"BV": "x3"},
        "type": "x",
        "properties": {"IND": "+", "NUM": "sg", "PERS": "3"}
      },
      "e8": {
        "label": "_new_a_1",
        "lnk": {"from": 4, "to": 7},
        "edges": {"ARG1": "x3"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "untensed", "PROG": "bool", "MOOD": "indicative"}
      },
      "x3": {
        "label": "_chef_n_1",
        "lnk": {"from": 8, "to": 12},
        "edges": {},
        "type": "x",
        "properties": {"IND": "+", "NUM": "sg", "PERS": "3"}
      },
      "_2": {
        "label": "def_explicit_q",
        "lnk": {"from": 13, "to": 18},
        "edges": {"BV": "x10"},
        "type": "x",
        "properties": {"NUM": "sg", "PERS": "3"}
      },
      "e14": {
        "label": "poss",
        "lnk": {"from": 13, "to": 18},
        "edges": {"ARG2": "x3", "ARG1": "x10"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "untensed", "PROG": "-", "MOOD": "indicative"}
      },
      "x10": {
        "label": "_soup_n_1",
        "lnk": {"from": 19, "to": 23},
        "edges": {},
        "type": "x",
        "properties": {"NUM": "sg", "PERS": "3"}
      },
      "e15": {
        "label": "_accidental_a_1",
        "lnk": {"from": 24, "to": 36},
        "edges": {"ARG1": "e16"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "untensed", "PROG": "-", "MOOD": "indicative"}
      },
      "e16": {
        "label": "_spill_v_1",
        "lnk": {"from": 37, "to": 44},
        "edges": {"ARG1": "x10"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "past", "PROG": "-", "MOOD": "indicative"}
      },
      "e18": {
        "label": "_quit_v_1",
        "lnk": {"from": 45, "to": 49},
        "edges": {"ARG1": "x3"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "past", "PROG": "-", "MOOD": "indicative"}
      },
      "e2": {
        "label": "_and_c",
        "lnk": {"from": 50, "to": 53},
        "edges": {"ARG2": "e20", "ARG1": "e18"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "past", "PROG": "-", "MOOD": "indicative"}
      },
      "e20": {
        "label": "_leave_v_1",
        "lnk": {"from": 54, "to": 59},
        "edges": {"ARG1": "x3"},
        "type": "e",
        "properties": {"PERF": "-", "SF": "prop", "TENSE": "past", "PROG": "-", "MOOD": "indicative"}
      }
    }
  }
"""

from pathlib import Path

import json

from delphin.lnk import Lnk
from delphin.eds import EDS, Node


CODEC_INFO = {
    'representation': 'eds',
}

HEADER = '['
JOINER = ','
FOOTER = ']'


def load(source):
    """
    Deserialize a EDS-JSON file (handle or filename) to EDS objects

    Args:
        source: filename or file object
    Returns:
        a list of EDS objects
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
    Deserialize a EDS-JSON string to EDS objects

    Args:
        s (str): a EDS-JSON string
    Returns:
        a list of EDS objects
    """
    data = json.loads(s)
    return [from_dict(d) for d in data]


def dump(es, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize EDS objects to a EDS-JSON file.

    Args:
        destination: filename or file object
        es: iterator of :class:`~delphin.eds.EDS` objects to
            serialize
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
    data = [to_dict(e, properties=properties, lnk=lnk)
            for e in es]
    if hasattr(destination, 'write'):
        json.dump(data, destination, indent=indent)
    else:
        destination = Path(destination).expanduser()
        with open(destination, 'w', encoding=encoding) as fh:
            json.dump(data, fh)


def dumps(es, properties=True, lnk=True, indent=False):
    """
    Serialize EDS objects to a EDS-JSON string.

    Args:
        es: iterator of :class:`~delphin.eds.EDS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        a EDS-JSON-serialization of the EDS objects
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    data = [to_dict(e, properties=properties, lnk=lnk)
            for e in es]
    return json.dumps(data, indent=indent)


def decode(s):
    """
    Deserialize a EDS object from a EDS-JSON string.
    """
    return from_dict(json.loads(s))


def encode(eds, properties=True, lnk=True, indent=False):
    """
    Serialize a EDS object to a EDS-JSON string.

    Args:
        e: a EDS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a EDS-JSON-serialization of the EDS object
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    d = to_dict(eds, properties=properties, lnk=lnk)
    return json.dumps(d, indent=indent)


def to_dict(eds, properties=True, lnk=True):
    """
    Encode the EDS as a dictionary suitable for JSON serialization.
    """
    # attempt to convert if necessary
    # if not isinstance(eds, EDS):
    #     eds = EDS.from_xmrs(eds, predicate_modifiers)

    nodes = {}
    for node in eds.nodes:
        nd = {
            'label': node.predicate,
            'edges': node.edges
        }
        if lnk and node.lnk is not None:
            nd['lnk'] = {'from': node.cfrom, 'to': node.cto}
        if node.type is not None:
            nd['type'] = node.type
        if properties:
            props = node.properties
            if props:
                nd['properties'] = props
        if node.carg is not None:
            nd['carg'] = node.carg
        nodes[node.id] = nd
    return {'top': eds.top, 'nodes': nodes}


def from_dict(d):
    """
    Decode a dictionary, as from :meth:`to_dict`, into an EDS object.
    """
    top = d.get('top')
    nodes = []
    for nodeid, node in d.get('nodes', {}).items():
        props = node.get('properties', None)
        nodetype = node.get('type')
        lnk = None
        if 'lnk' in node:
            lnk = Lnk.charspan(node['lnk']['from'], node['lnk']['to'])
        nodes.append(
            Node(id=nodeid,
                 predicate=node['label'],
                 type=nodetype,
                 edges=node.get('edges', {}),
                 properties=props,
                 carg=node.get('carg'),
                 lnk=lnk))
    nodes.sort(key=lambda n: (n.cfrom, -n.cto))
    return EDS(top, nodes=nodes)
