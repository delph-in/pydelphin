
delphin.codecs.mrsprolog
========================

.. automodule:: delphin.codecs.mrsprolog

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       psoa(h0,e2,
         [rel('_the_q',h4,
              [attrval('ARG0',x3),
               attrval('RSTR',h5),
               attrval('BODY',h6)]),
          rel('_new_a_1',h7,
              [attrval('ARG0',e8),
               attrval('ARG1',x3)]),
          rel('_chef_n_1',h7,
              [attrval('ARG0',x3)]),
          rel('def_explicit_q',h9,
              [attrval('ARG0',x10),
               attrval('RSTR',h11),
               attrval('BODY',h12)]),
          rel('poss',h13,
              [attrval('ARG0',e14),
               attrval('ARG1',x10),
               attrval('ARG2',x3)]),
          rel('_soup_n_1',h13,
              [attrval('ARG0',x10)]),
          rel('_accidental_a_1',h7,
              [attrval('ARG0',e15),
               attrval('ARG1',e16)]),
          rel('_spill_v_1',h7,
              [attrval('ARG0',e16),
               attrval('ARG1',x10),
               attrval('ARG2',i17)]),
          rel('_quit_v_1',h1,
              [attrval('ARG0',e18),
               attrval('ARG1',x3),
               attrval('ARG2',i19)]),
          rel('_and_c',h1,
              [attrval('ARG0',e2),
               attrval('ARG1',e18),
               attrval('ARG2',e20)]),
          rel('_leave_v_1',h1,
              [attrval('ARG0',e20),
               attrval('ARG1',x3),
               attrval('ARG2',i21)])],
         hcons([qeq(h0,h1),qeq(h5,h7),qeq(h11,h13)]))


   Serialization Functions
   -----------------------

   .. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

   .. function:: dumps(ms, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

   .. function:: encode(m, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.
