
delphin.codecs.dmrx
===================

.. automodule:: delphin.codecs.dmrx

   Example:

   * *The new chef whose soup accidentally spilled quit and left.*

     ::

       <dmrs cfrom="-1" cto="-1" index="10009" top="10008">
         <node cfrom="0" cto="3" nodeid="10000">
           <realpred lemma="the" pos="q" />
           <sortinfo />
         </node>
         <node cfrom="4" cto="7" nodeid="10001">
           <realpred lemma="new" pos="a" sense="1" />
           <sortinfo MOOD="indicative" PERF="-" PROG="bool" SF="prop" TENSE="untensed" cvarsort="e" />
         </node>
         <node cfrom="8" cto="12" nodeid="10002">
           <realpred lemma="chef" pos="n" sense="1" />
           <sortinfo IND="+" NUM="sg" PERS="3" cvarsort="x" />
         </node>
         <node cfrom="13" cto="18" nodeid="10003">
           <gpred>def_explicit_q</gpred>
           <sortinfo />
         </node>
         <node cfrom="13" cto="18" nodeid="10004">
           <gpred>poss</gpred>
           <sortinfo MOOD="indicative" PERF="-" PROG="-" SF="prop" TENSE="untensed" cvarsort="e" />
         </node>
         <node cfrom="19" cto="23" nodeid="10005">
           <realpred lemma="soup" pos="n" sense="1" />
           <sortinfo NUM="sg" PERS="3" cvarsort="x" />
         </node>
         <node cfrom="24" cto="36" nodeid="10006">
           <realpred lemma="accidental" pos="a" sense="1" />
           <sortinfo MOOD="indicative" PERF="-" PROG="-" SF="prop" TENSE="untensed" cvarsort="e" />
         </node>
         <node cfrom="37" cto="44" nodeid="10007">
           <realpred lemma="spill" pos="v" sense="1" />
           <sortinfo MOOD="indicative" PERF="-" PROG="-" SF="prop" TENSE="past" cvarsort="e" />
         </node>
         <node cfrom="45" cto="49" nodeid="10008">
           <realpred lemma="quit" pos="v" sense="1" />
           <sortinfo MOOD="indicative" PERF="-" PROG="-" SF="prop" TENSE="past" cvarsort="e" />
         </node>
         <node cfrom="50" cto="53" nodeid="10009">
           <realpred lemma="and" pos="c" />
           <sortinfo MOOD="indicative" PERF="-" PROG="-" SF="prop" TENSE="past" cvarsort="e" />
         </node>
         <node cfrom="54" cto="59" nodeid="10010">
           <realpred lemma="leave" pos="v" sense="1" />
           <sortinfo MOOD="indicative" PERF="-" PROG="-" SF="prop" TENSE="past" cvarsort="e" />
         </node>
         <link from="10000" to="10002">
           <rargname>RSTR</rargname>
           <post>H</post>
         </link>
         <link from="10001" to="10002">
           <rargname>ARG1</rargname>
           <post>EQ</post>
         </link>
         <link from="10003" to="10005">
           <rargname>RSTR</rargname>
           <post>H</post>
         </link>
         <link from="10004" to="10005">
           <rargname>ARG1</rargname>
           <post>EQ</post>
         </link>
         <link from="10004" to="10002">
           <rargname>ARG2</rargname>
           <post>NEQ</post>
         </link>
         <link from="10006" to="10007">
           <rargname>ARG1</rargname>
           <post>EQ</post>
         </link>
         <link from="10007" to="10005">
           <rargname>ARG1</rargname>
           <post>NEQ</post>
         </link>
         <link from="10008" to="10002">
           <rargname>ARG1</rargname>
           <post>NEQ</post>
         </link>
         <link from="10009" to="10008">
           <rargname>ARG1</rargname>
           <post>EQ</post>
         </link>
         <link from="10009" to="10010">
           <rargname>ARG2</rargname>
           <post>EQ</post>
         </link>
         <link from="10010" to="10002">
           <rargname>ARG1</rargname>
           <post>NEQ</post>
         </link>
         <link from="10007" to="10002">
           <rargname>MOD</rargname>
           <post>EQ</post>
         </link>
         <link from="10010" to="10008">
           <rargname>MOD</rargname>
           <post>EQ</post>
         </link>
       </dmrs>


   Module Constants
   ----------------

   .. data:: HEADER

      `'<dmrs-list>'`

   .. data:: JOINER

      `''`

   .. data:: FOOTER

      `'</dmrs-list>'`

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
