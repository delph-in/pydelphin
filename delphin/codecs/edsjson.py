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
        "edges": {"BV": "x3"},
        "lnk": {"from": 0, "to": 3}
      },
      "e8": {
        "label": "_new_a_1",
        "edges": {"ARG1": "x3"},
        "lnk": {"from": 4, "to": 7},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "untensed", "MOOD": "indicative", "PROG": "bool", "PERF": "-"}
      },
      "x3": {
        "label": "_chef_n_1",
        "edges": {},
        "lnk": {"from": 8, "to": 12},
        "type": "x",
        "properties": {"PERS": "3", "NUM": "sg", "IND": "+"}
      },
      "_2": {
        "label": "def_explicit_q",
        "edges": {"BV": "x10"},
        "lnk": {"from": 13, "to": 18}
      },
      "e14": {
        "label": "poss",
        "edges": {"ARG1": "x10", "ARG2": "x3"},
        "lnk": {"from": 13, "to": 18},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "untensed", "MOOD": "indicative", "PROG": "-", "PERF": "-"}
      },
      "x10": {
        "label": "_soup_n_1",
        "edges": {},
        "lnk": {"from": 19, "to": 23},
        "type": "x",
        "properties": {"PERS": "3", "NUM": "sg"}
      },
      "e15": {
        "label": "_accidental_a_1",
        "edges": {"ARG1": "e16"},
        "lnk": {"from": 24, "to": 36},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "untensed", "MOOD": "indicative", "PROG": "-", "PERF": "-"}
      },
      "e16": {
        "label": "_spill_v_1",
        "edges": {"ARG1": "x10"},
        "lnk": {"from": 37, "to": 44},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-"}
      },
      "e18": {
        "label": "_quit_v_1",
        "edges": {"ARG1": "x3"},
        "lnk": {"from": 45, "to": 49},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-"}
      },
      "e2": {
        "label": "_and_c",
        "edges": {"ARG1": "e18", "ARG2": "e20"},
        "lnk": {"from": 50, "to": 53},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-"}
      },
      "e20": {
        "label": "_leave_v_1",
        "edges": {"ARG1": "x3"},
        "lnk": {"from": 54, "to": 59},
        "type": "e",
        "properties": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-"}
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
