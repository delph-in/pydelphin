
delphin.codecs.mrsjson
======================

.. automodule:: delphin.codecs.mrsjson

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


   Module Constants
   ----------------

   .. data:: HEADER

      `'['`

   .. data:: JOINER

      `','`

   .. data:: FOOTER

      `']'`


   Deserialization Functions
   -------------------------

   .. function:: load(source)

      See the :func:`load` codec API documentation.

   .. function:: loads(s)

      See the :func:`loads` codec API documentation.

   .. function:: decode(s)

      See the :func:`decode` codec API documentation.


   Serialization Functions
   -----------------------

   .. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

   .. function:: dumps(ms, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

   .. function:: encode(m, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.


   Complementary Functions
   -----------------------

   .. autofunction:: from_dict
   .. autofunction:: to_dict
