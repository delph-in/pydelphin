
delphin.codecs.edsjson
======================

.. automodule:: delphin.codecs.edsjson

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

