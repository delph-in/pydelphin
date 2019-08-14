
delphin.codecs.dmrsjson
=======================

.. automodule:: delphin.codecs.dmrsjson

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       {
         "top": 10008,
         "index": 10009,
         "nodes": [
           {
             "nodeid": 10000,
             "predicate": "_the_q",
             "lnk": {"from": 0, "to": 3}
           },
           {
             "nodeid": 10001,
             "predicate": "_new_a_1",
             "sortinfo": {"SF": "prop", "TENSE": "untensed", "MOOD": "indicative", "PROG": "bool", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 4, "to": 7}
           },
           {
             "nodeid": 10002,
             "predicate": "_chef_n_1",
             "sortinfo": {"PERS": "3", "NUM": "sg", "IND": "+", "cvarsort": "x"},
             "lnk": {"from": 8, "to": 12}
           },
           {
             "nodeid": 10003,
             "predicate": "def_explicit_q",
             "lnk": {"from": 13, "to": 18}
           },
           {
             "nodeid": 10004,
             "predicate": "poss",
             "sortinfo": {"SF": "prop", "TENSE": "untensed", "MOOD": "indicative", "PROG": "-", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 13, "to": 18}
           },
           {
             "nodeid": 10005,
             "predicate": "_soup_n_1",
             "sortinfo": {"PERS": "3", "NUM": "sg", "cvarsort": "x"},
             "lnk": {"from": 19, "to": 23}
           },
           {
             "nodeid": 10006,
             "predicate": "_accidental_a_1",
             "sortinfo": {"SF": "prop", "TENSE": "untensed", "MOOD": "indicative", "PROG": "-", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 24, "to": 36}
           },
           {
             "nodeid": 10007,
             "predicate": "_spill_v_1",
             "sortinfo": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 37, "to": 44}
           },
           {
             "nodeid": 10008,
             "predicate": "_quit_v_1",
             "sortinfo": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 45, "to": 49}
           },
           {
             "nodeid": 10009,
             "predicate": "_and_c",
             "sortinfo": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 50, "to": 53}
           },
           {
             "nodeid": 10010,
             "predicate": "_leave_v_1",
             "sortinfo": {"SF": "prop", "TENSE": "past", "MOOD": "indicative", "PROG": "-", "PERF": "-", "cvarsort": "e"},
             "lnk": {"from": 54, "to": 59}
           }
         ],
         "links": [
           {"from": 10000, "to": 10002, "rargname": "RSTR", "post": "H"},
           {"from": 10001, "to": 10002, "rargname": "ARG1", "post": "EQ"},
           {"from": 10003, "to": 10005, "rargname": "RSTR", "post": "H"},
           {"from": 10004, "to": 10005, "rargname": "ARG1", "post": "EQ"},
           {"from": 10004, "to": 10002, "rargname": "ARG2", "post": "NEQ"},
           {"from": 10006, "to": 10007, "rargname": "ARG1", "post": "EQ"},
           {"from": 10007, "to": 10005, "rargname": "ARG1", "post": "NEQ"},
           {"from": 10008, "to": 10002, "rargname": "ARG1", "post": "NEQ"},
           {"from": 10009, "to": 10008, "rargname": "ARG1", "post": "EQ"},
           {"from": 10009, "to": 10010, "rargname": "ARG2", "post": "EQ"},
           {"from": 10010, "to": 10002, "rargname": "ARG1", "post": "NEQ"},
           {"from": 10007, "to": 10002, "rargname": "MOD", "post": "EQ"},
           {"from": 10010, "to": 10008, "rargname": "MOD", "post": "EQ"}
         ]
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
