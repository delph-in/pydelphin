
delphin.codecs.mrx
==================

.. automodule:: delphin.codecs.mrx

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       <mrs cfrom="-1" cto="-1"><label vid="0" /><var sort="e" vid="2">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>past</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>-</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var>
         <ep cfrom="0" cto="3"><realpred lemma="the" pos="q" /><label vid="4" />
         <fvpair><rargname>ARG0</rargname><var sort="x" vid="3">
         <extrapair><path>PERS</path><value>3</value></extrapair>
         <extrapair><path>NUM</path><value>sg</value></extrapair>
         <extrapair><path>IND</path><value>+</value></extrapair></var></fvpair>
         <fvpair><rargname>RSTR</rargname><var sort="h" vid="5" /></fvpair>
         <fvpair><rargname>BODY</rargname><var sort="h" vid="6" /></fvpair></ep>
         <ep cfrom="4" cto="7"><realpred lemma="new" pos="a" sense="1" /><label vid="7" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="8">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>untensed</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>bool</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="x" vid="3" /></fvpair></ep>
         <ep cfrom="8" cto="12"><realpred lemma="chef" pos="n" sense="1" /><label vid="7" />
         <fvpair><rargname>ARG0</rargname><var sort="x" vid="3" /></fvpair></ep>
         <ep cfrom="13" cto="18"><pred>def_explicit_q</pred><label vid="9" />
         <fvpair><rargname>ARG0</rargname><var sort="x" vid="10">
         <extrapair><path>PERS</path><value>3</value></extrapair>
         <extrapair><path>NUM</path><value>sg</value></extrapair></var></fvpair>
         <fvpair><rargname>RSTR</rargname><var sort="h" vid="11" /></fvpair>
         <fvpair><rargname>BODY</rargname><var sort="h" vid="12" /></fvpair></ep>
         <ep cfrom="13" cto="18"><pred>poss</pred><label vid="13" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="14">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>untensed</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>-</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="x" vid="10" /></fvpair>
         <fvpair><rargname>ARG2</rargname><var sort="x" vid="3" /></fvpair></ep>
         <ep cfrom="19" cto="23"><realpred lemma="soup" pos="n" sense="1" /><label vid="13" />
         <fvpair><rargname>ARG0</rargname><var sort="x" vid="10" /></fvpair></ep>
         <ep cfrom="24" cto="36"><realpred lemma="accidental" pos="a" sense="1" /><label vid="7" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="15">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>untensed</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>-</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="e" vid="16">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>past</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>-</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var></fvpair></ep>
         <ep cfrom="37" cto="44"><realpred lemma="spill" pos="v" sense="1" /><label vid="7" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="16" /></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="x" vid="10" /></fvpair>
         <fvpair><rargname>ARG2</rargname><var sort="i" vid="17" /></fvpair></ep>
         <ep cfrom="45" cto="49"><realpred lemma="quit" pos="v" sense="1" /><label vid="1" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="18">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>past</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>-</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="x" vid="3" /></fvpair>
         <fvpair><rargname>ARG2</rargname><var sort="i" vid="19" /></fvpair></ep>
         <ep cfrom="50" cto="53"><realpred lemma="and" pos="c" /><label vid="1" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="2" /></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="e" vid="18" /></fvpair>
         <fvpair><rargname>ARG2</rargname><var sort="e" vid="20">
         <extrapair><path>SF</path><value>prop</value></extrapair>
         <extrapair><path>TENSE</path><value>past</value></extrapair>
         <extrapair><path>MOOD</path><value>indicative</value></extrapair>
         <extrapair><path>PROG</path><value>-</value></extrapair>
         <extrapair><path>PERF</path><value>-</value></extrapair></var></fvpair></ep>
         <ep cfrom="54" cto="59"><realpred lemma="leave" pos="v" sense="1" /><label vid="1" />
         <fvpair><rargname>ARG0</rargname><var sort="e" vid="20" /></fvpair>
         <fvpair><rargname>ARG1</rargname><var sort="x" vid="3" /></fvpair>
         <fvpair><rargname>ARG2</rargname><var sort="i" vid="21" /></fvpair></ep>
         <hcons hreln="qeq"><hi><var sort="h" vid="0" /></hi><lo><label vid="1" /></lo></hcons>
         <hcons hreln="qeq"><hi><var sort="h" vid="5" /></hi><lo><label vid="7" /></lo></hcons>
         <hcons hreln="qeq"><hi><var sort="h" vid="11" /></hi><lo><label vid="13" /></lo></hcons>
       </mrs>


   Module Constants
   ----------------

   .. data:: HEADER

      `'<mrs-list>'`

   .. data:: JOINER

      `''`

   .. data:: FOOTER

      `'</mrs-list>'`

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
