
delphin.codecs.simpledmrs
=========================

.. automodule:: delphin.codecs.simpledmrs

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       dmrs {
         ["The new chef whose soup accidentally spilled quit and left." top=10008 index=10009]
         10000 [_the_q<0:3>];
         10001 [_new_a_1<4:7> e SF=prop TENSE=untensed MOOD=indicative PROG=bool PERF=-];
         10002 [_chef_n_1<8:12> x PERS=3 NUM=sg IND=+];
         10003 [def_explicit_q<13:18>];
         10004 [poss<13:18> e SF=prop TENSE=untensed MOOD=indicative PROG=- PERF=-];
         10005 [_soup_n_1<19:23> x PERS=3 NUM=sg];
         10006 [_accidental_a_1<24:36> e SF=prop TENSE=untensed MOOD=indicative PROG=- PERF=-];
         10007 [_spill_v_1<37:44> e SF=prop TENSE=past MOOD=indicative PROG=- PERF=-];
         10008 [_quit_v_1<45:49> e SF=prop TENSE=past MOOD=indicative PROG=- PERF=-];
         10009 [_and_c<50:53> e SF=prop TENSE=past MOOD=indicative PROG=- PERF=-];
         10010 [_leave_v_1<54:59> e SF=prop TENSE=past MOOD=indicative PROG=- PERF=-];
         10000:RSTR/H -> 10002;
         10001:ARG1/EQ -> 10002;
         10003:RSTR/H -> 10005;
         10004:ARG1/EQ -> 10005;
         10004:ARG2/NEQ -> 10002;
         10006:ARG1/EQ -> 10007;
         10007:ARG1/NEQ -> 10005;
         10008:ARG1/NEQ -> 10002;
         10009:ARG1/EQ -> 10008;
         10009:ARG2/EQ -> 10010;
         10010:ARG1/NEQ -> 10002;
         10007:MOD/EQ -> 10002;
         10010:MOD/EQ -> 10008;
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

   .. function:: dump(ms, destination, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dump` codec API documentation.

   .. function:: dumps(ms, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`dumps` codec API documentation.

   .. function:: encode(m, properties=True, lnk=True, indent=False, encoding='utf-8')

      See the :func:`encode` codec API documentation.
