# -*- coding: utf-8 -*-

"""
DMRS-JSON serialization and deserialization.

Example:

* *The new chef whose soup accidentally spilled quit and left.*

::

  {
    "nodes": [
      {
        "sortinfo": {
          "cvarsort": "x"
        },
        "lnk": {
          "from": 0,
          "to": 3
        },
        "nodeid": 10000,
        "predicate": "_the_q"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "bool",
          "SF": "prop",
          "TENSE": "untensed"
        },
        "lnk": {
          "from": 4,
          "to": 7
        },
        "nodeid": 10001,
        "predicate": "_new_a_1"
      },
      {
        "sortinfo": {
          "cvarsort": "x",
          "IND": "+",
          "NUM": "sg",
          "PERS": "3"
        },
        "lnk": {
          "from": 8,
          "to": 12
        },
        "nodeid": 10002,
        "predicate": "_chef_n_1"
      },
      {
        "sortinfo": {
          "cvarsort": "x"
        },
        "lnk": {
          "from": 13,
          "to": 18
        },
        "nodeid": 10003,
        "predicate": "def_explicit_q"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "-",
          "SF": "prop",
          "TENSE": "untensed"
        },
        "lnk": {
          "from": 13,
          "to": 18
        },
        "nodeid": 10004,
        "predicate": "poss"
      },
      {
        "sortinfo": {
          "cvarsort": "x",
          "NUM": "sg",
          "PERS": "3"
        },
        "lnk": {
          "from": 19,
          "to": 23
        },
        "nodeid": 10005,
        "predicate": "_soup_n_1"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "-",
          "SF": "prop",
          "TENSE": "untensed"
        },
        "lnk": {
          "from": 24,
          "to": 36
        },
        "nodeid": 10006,
        "predicate": "_accidental_a_1"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "-",
          "SF": "prop",
          "TENSE": "past"
        },
        "lnk": {
          "from": 37,
          "to": 44
        },
        "nodeid": 10007,
        "predicate": "_spill_v_1"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "-",
          "SF": "prop",
          "TENSE": "past"
        },
        "lnk": {
          "from": 45,
          "to": 49
        },
        "nodeid": 10008,
        "predicate": "_quit_v_1"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "-",
          "SF": "prop",
          "TENSE": "past"
        },
        "lnk": {
          "from": 50,
          "to": 53
        },
        "nodeid": 10009,
        "predicate": "_and_c"
      },
      {
        "sortinfo": {
          "cvarsort": "e",
          "PERF": "-",
          "MOOD": "indicative",
          "PROG": "-",
          "SF": "prop",
          "TENSE": "past"
        },
        "lnk": {
          "from": 54,
          "to": 59
        },
        "nodeid": 10010,
        "predicate": "_leave_v_1"
      }
    ],
    "links": [
      {
        "from": 10007,
        "to": 10005,
        "post": "NEQ",
        "rargname": "ARG1"
      },
      {
        "from": 10000,
        "to": 10002,
        "post": "H",
        "rargname": "RSTR"
      },
      {
        "from": 10003,
        "to": 10005,
        "post": "H",
        "rargname": "RSTR"
      },
      {
        "from": 10008,
        "to": 10002,
        "post": "NEQ",
        "rargname": "ARG1"
      },
      {
        "from": 10009,
        "to": 10008,
        "post": "EQ",
        "rargname": "ARG1"
      },
      {
        "from": 10009,
        "to": 10010,
        "post": "EQ",
        "rargname": "ARG2"
      },
      {
        "from": 10010,
        "to": 10002,
        "post": "NEQ",
        "rargname": "ARG1"
      },
      {
        "from": 10004,
        "to": 10005,
        "post": "EQ",
        "rargname": "ARG1"
      },
      {
        "from": 10004,
        "to": 10002,
        "post": "NEQ",
        "rargname": "ARG2"
      },
      {
        "from": 10006,
        "to": 10007,
        "post": "EQ",
        "rargname": "ARG1"
      },
      {
        "from": 10001,
        "to": 10002,
        "post": "EQ",
        "rargname": "ARG1"
      },
      {
        "from": 10010,
        "to": 10008,
        "post": "EQ",
        "rargname": "MOD"
      },
      {
        "from": 10007,
        "to": 10002,
        "post": "EQ",
        "rargname": "MOD"
      }
    ],
    "index": 10009,
    "top": 10008
  }

"""

import json

from delphin.lnk import Lnk
from delphin.dmrs import (
    DMRS,
    Node,
    Link,
    CVARSORT,
)


HEADER = '['
JOINER = ','
FOOTER = ']'


def load(source):
    """
    Deserialize a DMRS-JSON file (handle or filename) to DMRS objects

    Args:
        source: filename or file object
    Returns:
        a list of DMRS objects
    """
    if hasattr(source, 'read'):
        data = json.load(source)
    else:
        with open(source) as fh:
            data = json.load(fh)
    return [from_dict(d) for d in data]


def loads(s):
    """
    Deserialize a DMRS-JSON string to DMRS objects

    Args:
        s (str): a DMRS-JSON string
    Returns:
        a list of DMRS objects
    """
    data = json.loads(s)
    return [from_dict(d) for d in data]


def dump(ds, destination, properties=True, lnk=True,
         indent=False, encoding='utf-8'):
    """
    Serialize DMRS objects to a DMRS-JSON file.

    Args:
        destination: filename or file object
        ds: iterator of :class:`~delphin.dmrs.DMRS` objects to
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
    data = [to_dict(d, properties=properties, lnk=lnk) for d in ds]
    if hasattr(destination, 'write'):
        json.dump(data, destination, indent=indent)
    else:
        with open(destination, 'w', encoding=encoding) as fh:
            json.dump(data, fh)


def dumps(ds, properties=True, lnk=True, indent=False):
    """
    Serialize DMRS objects to a DMRS-JSON string.

    Args:
        ds: iterator of :class:`~delphin.dmrs.DMRS` objects to
            serialize
        properties: if `True`, encode variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent: if `True`, adaptively indent; if `False` or `None`,
            don't indent; if a non-negative integer N, indent N spaces
            per level
    Returns:
        a DMRS-JSON-serialization of the DMRS objects
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    data = [to_dict(d, properties=properties, lnk=lnk) for d in ds]
    return json.dumps(data, indent=indent)


def decode(s):
    """
    Deserialize a DMRS object from a DMRS-JSON string.
    """
    return from_dict(json.loads(s))


def encode(d, properties=True, lnk=True, indent=False):
    """
    Serialize a DMRS object to a DMRS-JSON string.

    Args:
        d: a DMRS object
        properties (bool): if `False`, suppress variable properties
        lnk: if `False`, suppress surface alignments and strings
        indent (bool, int): if `True` or an integer value, add
            newlines and indentation
    Returns:
        a DMRS-JSON-serialization of the DMRS object
    """
    if indent is False:
        indent = None
    elif indent is True:
        indent = 2
    return json.dumps(to_dict(d, properties=properties, lnk=lnk),
                      indent=indent)


def to_dict(dmrs, properties=True, lnk=True):
    """
    Encode *dmrs* as a dictionary suitable for JSON serialization.
    """
    # attempt to convert if necessary
    # if not isinstance(dmrs, DMRS):
    #     dmrs = DMRS.from_xmrs(dmrs)

    nodes = []
    for node in dmrs.nodes:
        n = dict(nodeid=node.id,
                 predicate=node.predicate)
        if properties and node.sortinfo:
            n['sortinfo'] = node.sortinfo
        if node.carg is not None:
            n['carg'] = node.carg
        if lnk:
            if node.lnk:
                n['lnk'] = {'from': node.cfrom, 'to': node.cto}
            if node.surface:
                n['surface'] = node.surface
            if node.base:
                n['base'] = node.base
        nodes.append(n)
    links = []
    for link in dmrs.links:
        links.append({
            'from': link.start, 'to': link.end,
            'rargname': link.role, 'post': link.post
        })
    d = dict(nodes=nodes, links=links)
    if dmrs.top is not None:  # could be 0
        d['top'] = dmrs.top
    if dmrs.index:
        d['index'] = dmrs.index
    if lnk:
        if dmrs.lnk:
            d['lnk'] = {'from': dmrs.cfrom, 'to': dmrs.cto}
        if dmrs.surface:
            d['surface'] = dmrs.surface
    if dmrs.identifier is not None:
        d['identifier'] = dmrs.identifier
    return d


def from_dict(d):
    """
    Decode a dictionary, as from :func:`to_dict`, into a DMRS object.
    """
    def _lnk(x):
        return None if x is None else Lnk.charspan(x['from'], x['to'])
    nodes = []
    for node in d.get('nodes', []):
        properties = dict(node.get('sortinfo', {}))  # make a copy
        type = None
        if CVARSORT in properties:
            type = properties.pop(CVARSORT)
        nodes.append(Node(
            node['nodeid'],
            node['predicate'],
            type=type,
            properties=properties,
            carg=node.get('carg'),
            lnk=_lnk(node.get('lnk')),
            surface=node.get('surface'),
            base=node.get('base')))
    links = []
    for link in d.get('links', []):
        links.append(Link(
            link['from'],
            link['to'],
            link.get('rargname'),
            link.get('post')))
    return DMRS(
        top=d.get('top'),
        index=d.get('index'),
        nodes=nodes,
        links=links,
        lnk=_lnk(d.get('lnk')),
        surface=d.get('surface'),
        identifier=d.get('identifier')
    )
