
delphin.codecs.simplemrs
========================

.. automodule:: delphin.codecs.simplemrs

   SimpleMRS is a format for Minimal Recursion Semantics that aims to
   be readable equally by humans and machines.

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     .. code:: simplemrs

        [ TOP: h0
          INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
          RELS: < [ _the_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
                  [ _new_a_1<4:7> LBL: h7 ARG0: e8 [ e SF: prop TENSE: untensed MOOD: indicative PROG: bool PERF: - ] ARG1: x3 ]
                  [ _chef_n_1<8:12> LBL: h7 ARG0: x3 ]
                  [ def_explicit_q<13:18> LBL: h9 ARG0: x10 [ x PERS: 3 NUM: sg ] RSTR: h11 BODY: h12 ]
                  [ poss<13:18> LBL: h13 ARG0: e14 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: x10 ARG2: x3 ]
                  [ _soup_n_1<19:23> LBL: h13 ARG0: x10 ]
                  [ _accidental_a_1<24:36> LBL: h7 ARG0: e15 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: e16 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] ]
                  [ _spill_v_1<37:44> LBL: h7 ARG0: e16 ARG1: x10 ARG2: i17 ]
                  [ _quit_v_1<45:49> LBL: h1 ARG0: e18 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] ARG1: x3 ARG2: i19 ]
                  [ _and_c<50:53> LBL: h1 ARG0: e2 ARG1: e18 ARG2: e20 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] ]
                  [ _leave_v_1<54:59> LBL: h1 ARG0: e20 ARG1: x3 ARG2: i21 ] >
          HCONS: < h0 qeq h1 h5 qeq h7 h11 qeq h13 > ]


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
