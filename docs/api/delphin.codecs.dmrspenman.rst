
delphin.codecs.dmrspenman
=========================

.. automodule:: delphin.codecs.dmrspenman

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       (e9 / _quit_v_1
         :lnk "<45:49>"
         :cvarsort e
         :sf prop
         :tense past
         :mood indicative
         :prog -
         :perf -
         :ARG1-NEQ (x3 / _chef_n_1
           :lnk "<8:12>"
           :cvarsort x
           :pers 3
           :num sg
           :ind +
           :RSTR-H-of (q1 / _the_q
             :lnk "<0:3>")
           :ARG1-EQ-of (e2 / _new_a_1
             :lnk "<4:7>"
             :cvarsort e
             :sf prop
             :tense untensed
             :mood indicative
             :prog bool
             :perf -)
           :ARG2-NEQ-of (e5 / poss
             :lnk "<13:18>"
             :cvarsort e
             :sf prop
             :tense untensed
             :mood indicative
             :prog -
             :perf -
             :ARG1-EQ (x6 / _soup_n_1
               :lnk "<19:23>"
               :cvarsort x
               :pers 3
               :num sg
               :RSTR-H-of (q4 / def_explicit_q
                 :lnk "<13:18>")))
           :MOD-EQ-of (e8 / _spill_v_1
             :lnk "<37:44>"
             :cvarsort e
             :sf prop
             :tense past
             :mood indicative
             :prog -
             :perf -
             :ARG1-NEQ x6
             :ARG1-EQ-of (e7 / _accidental_a_1
               :lnk "<24:36>"
               :cvarsort e
               :sf prop
               :tense untensed
               :mood indicative
               :prog -
               :perf -)))
         :ARG1-EQ-of (e10 / _and_c
           :lnk "<50:53>"
           :cvarsort e
           :sf prop
           :tense past
           :mood indicative
           :prog -
           :perf -
           :ARG2-EQ (e11 / _leave_v_1
             :lnk "<54:59>"
             :cvarsort e
             :sf prop
             :tense past
             :mood indicative
             :prog -
             :perf -
             :ARG1-NEQ x3
             :MOD-EQ e9)))


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

   .. autofunction:: from_triples
   .. autofunction:: to_triples
