
delphin.codecs.edspenman
========================

.. automodule:: delphin.codecs.edspenman

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       (e18 / _quit_v_1
         :lnk "<45:49>"
         :type e
         :sf prop
         :tense past
         :mood indicative
         :prog -
         :perf -
         :ARG1 (x3 / _chef_n_1
           :lnk "<8:12>"
           :type x
           :pers 3
           :num sg
           :ind +
           :BV-of (_1 / _the_q
             :lnk "<0:3>")
           :ARG1-of (e8 / _new_a_1
             :lnk "<4:7>"
             :type e
             :sf prop
             :tense untensed
             :mood indicative
             :prog bool
             :perf -)
           :ARG2-of (e14 / poss
             :lnk "<13:18>"
             :type e
             :sf prop
             :tense untensed
             :mood indicative
             :prog -
             :perf -
             :ARG1 (x10 / _soup_n_1
               :lnk "<19:23>"
               :type x
               :pers 3
               :num sg
               :BV-of (_2 / def_explicit_q
                 :lnk "<13:18>")
               :ARG1-of (e16 / _spill_v_1
                 :lnk "<37:44>"
                 :type e
                 :sf prop
                 :tense past
                 :mood indicative
                 :prog -
                 :perf -
                 :ARG1-of (e15 / _accidental_a_1
                   :lnk "<24:36>"
                   :type e
                   :sf prop
                   :tense untensed
                   :mood indicative
                   :prog -
                   :perf -)))))
         :ARG1-of (e2 / _and_c
           :lnk "<50:53>"
           :type e
           :sf prop
           :tense past
           :mood indicative
           :prog -
           :perf -
           :ARG2 (e20 / _leave_v_1
             :lnk "<54:59>"
             :type e
             :sf prop
             :tense past
             :mood indicative
             :prog -
             :perf -
             :ARG1 x3)))


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
