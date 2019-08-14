
delphin.codecs.indexedmrs
=========================

.. automodule:: delphin.codecs.indexedmrs

   The Indexed MRS format does not include role names such as `ARG1`,
   `ARG2`, etc., so the order of the arguments in a predication is
   important. For this reason, serialization with the Indexed MRS
   format requires the use of a SEM-I (see the :mod:`delphin.semi`
   module).

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       < h0, e2:PROP:PAST:INDICATIVE:-:-,
         { h4:_the_q<0:3>(x3:3:SG:GENDER:+:PT, h5, h6),
           h7:_new_a_1<4:7>(e8:PROP:UNTENSED:INDICATIVE:BOOL:-, x3),
           h7:_chef_n_1<8:12>(x3),
           h9:def_explicit_q<13:18>(x10:3:SG:GENDER:BOOL:PT, h11, h12),
           h13:poss<13:18>(e14:PROP:UNTENSED:INDICATIVE:-:-, x10, x3),
           h13:_soup_n_1<19:23>(x10),
           h7:_accidental_a_1<24:36>(e15:PROP:UNTENSED:INDICATIVE:-:-, e16:PROP:PAST:INDICATIVE:-:-),
           h7:_spill_v_1<37:44>(e16, x10, i17),
           h1:_quit_v_1<45:49>(e18:PROP:PAST:INDICATIVE:-:-, x3, i19),
           h1:_and_c<50:53>(e2, e18, e20:PROP:PAST:INDICATIVE:-:-),
           h1:_leave_v_1<54:59>(e20, x3, i21) },
         { h0 qeq h1,
           h5 qeq h7,
           h11 qeq h13 } >


   Deserialization Functions
   -------------------------

   .. function:: load(source, semi)

      See the :func:`load` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: loads(s, semi)

      See the :func:`loads` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: decode(s, semi)

      See the :func:`decode` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   Serialization Functions
   -----------------------

   .. function:: dump(ms, destination, semi, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: dumps(ms, semi, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS

   .. function:: encode(m, semi, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.

      **Extensions:**

      :param SemI semi: the semantic interface for the grammar
			that produced the MRS
