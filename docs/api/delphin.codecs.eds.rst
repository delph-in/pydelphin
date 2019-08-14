
delphin.codecs.eds
==================

.. automodule:: delphin.codecs.eds

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       {e18:
        _1:_the_q<0:3>[BV x3]
        e8:_new_a_1<4:7>{e SF prop, TENSE untensed, MOOD indicative, PROG bool, PERF -}[ARG1 x3]
        x3:_chef_n_1<8:12>{x PERS 3, NUM sg, IND +}[]
        _2:def_explicit_q<13:18>[BV x10]
        e14:poss<13:18>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x10, ARG2 x3]
        x10:_soup_n_1<19:23>{x PERS 3, NUM sg}[]
        e15:_accidental_a_1<24:36>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 e16]
        e16:_spill_v_1<37:44>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x10]
        e18:_quit_v_1<45:49>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x3]
        e2:_and_c<50:53>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 e18, ARG2 e20]
        e20:_leave_v_1<54:59>{e SF prop, TENSE past, MOOD indicative, PROG -, PERF -}[ARG1 x3]
       }


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

   .. function:: dump(ms, destination, properties=True, lnk=True, show_status=False, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

      **Extensions:**

      :param bool show_status: if `True`, indicate disconnected
                               components

   .. function:: dumps(ms, properties=True, lnk=True, show_status=False, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

      **Extensions:**

      :param bool show_status: if `True`, indicate disconnected
                               components

   .. function:: encode(m, properties=True, lnk=True, show_status=False, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.

      **Extensions:**

      :param bool show_status: if `True`, indicate disconnected
                               components
