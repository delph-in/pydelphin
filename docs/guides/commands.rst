
PyDelphin at the Command Line
=============================

PyDelphin is primarily a library for creating more complex software,
but some functions are directly useful as commands. To facilitate this
usage, the :command:`delphin` command (:command:`delphin.exe` on
Windows) provides an entry point to a number of subcommands,
including: `convert`_, `select`_, `mkprof`_, `process`_, `compare`_,
and `repp`_. These subcommands are command-line front-ends to the
functions defined in :mod:`delphin.commands`.

Usage
-----

The :command:`delphin` command becomes available when PyDelphin is
:doc:`installed <setup>`.

.. code:: console

   $ delphin --help
   usage: delphin [-h] [-V]  ...

   PyDelphin command-line interface

   optional arguments:
     -h, --help     show this help message and exit
     -V, --version  show program's version number and exit

   available subcommands:

       convert      Convert DELPH-IN Semantics representations
       select       Select data from [incr tsdb()] test suites
       mkprof       Create [incr tsdb()] test suites
       process      Process [incr tsdb()] test suites using ACE
       compare      Compare MRS results across test suites
       repp         Tokenize sentences using REPP

   $ delphin --version
   delphin 1.0.0

PyDelphin developers may find it useful to run the command without
installing, which is available via the `delphin.main` module:

.. code:: console

   ~/pydelphin$ python3 -m delphin.main --version
   delphin 1.0.0

This guide assumes you have installed PyDelphin and thus have the
:command:`delphin` command available.


Subcommands
-----------

.. _convert-tutorial:

convert
'''''''

The :command:`convert` subcommand enables conversion of various
DELPH-IN Semantics representations. The ``--from`` and ``--to``
options select the source and target representations (the default for
both is `simplemrs`). Here is an example of converting :mod:`SimpleMRS
<delphin.codecs.simplemrs>` to :mod:`JSON-serialized DMRS
<delphin.codecs.dmrsjson>`:

.. code:: console

  $ echo '[ "It rains." TOP: h0 RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ]' \
  > | delphin convert --to dmrs-json
  [{"surface": "It rains.", "links": [{"to": 10000, "rargname": null, "from": 0, "post": "H"}], "nodes": [{"sortinfo": {"cvarsort": "e"}, "lnk": {"to": 8, "from": 3}, "nodeid": 10000, "predicate": "_rain_v_1"}]}]

As the default for ``--from`` and ``--to`` is ``simplemrs``, it can be
used to easily "pretty-print" an MRS (if you execute this in a
terminal and have `delphin.highlight
<https://github.com/delph-in/delphin.highlight>`_ installed, you'll
notice syntax highlighting as well):

.. code:: console

   $ echo '[ "It rains." TOP: h0 RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ]' \
   > | delphin convert --indent
   [ "It rains."
     TOP: h0
     RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] >
     HCONS: < h0 qeq h1 > ]

Some formats are export-only, such as :mod:`mrsprolog <delphin.codecs.mrsprolog>`:

.. code:: console

   $ echo '[ "It rains." TOP: h0 RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ]' \
   > | delphin convert --to mrsprolog --indent
   psoa(h0,
     [rel('_rain_v_1',h1,
          [attrval('ARG0',e2)])],
     hcons([qeq(h0,h1)]))

The full list of codecs that PyDelphin can use can be obtained with
the ``--list`` option, which groups them by their representation and
indicates if they can read (``r``) or write (``w``) the format.

.. code:: console

   $ delphin convert --list
   DMRS
	dmrsjson    	r/w
	dmrspenman  	r/w
	dmrstikz    	-/w
	dmrx        	r/w
	simpledmrs  	r/w
   EDS
	eds         	r/w
	edsjson     	r/w
	edspenman   	r/w
   MRS
	ace         	r/-
	indexedmrs  	r/w
	mrsjson     	r/w
	mrsprolog   	-/w
	mrx         	r/w
	simplemrs   	r/w

Try ``delphin convert --help`` for more information.


.. _select-tutorial:

select
''''''

The :command:`select` subcommand selects data from an [incr tsdb()]
profile using TSQL_ queries. For example, if you want to get the
``i-id`` and ``i-input`` fields from a profile, do this:

.. _TSQL: http://moin.delph-in.net/TsqlRfc

.. code:: console

   $ delphin select 'i-id i-input from item' ~/grammars/jacy/tsdb/gold/mrs/
   11@雨 が 降っ た ．
   21@太郎 が 吠え た ．
   [..]


In many cases, the ``from`` clause of the query is not necessary, and
the appropriate tables will be selected automatically.  Fields from
multiple tables can be used and the tables containing them will be
automatically joined:

.. code:: console

   $ delphin select 'i-id mrs' ~/grammars/jacy/tsdb/gold/mrs/
   11@[ LTOP: h1 INDEX: e2 ... ]
   [..]

The results can be filtered by providing ``where`` clauses:

.. code:: console

   $ delphin select 'i-id i-input where i-input ~ "雨"' ~/grammars/jacy/tsdb/gold/mrs/
   11@雨 が 降っ た ．
   71@太郎 が タバコ を 次郎 に 雨 が 降る と 賭け た ．
   81@太郎 が 雨 が 降っ た こと を 知っ て い た ．

Try ``delphin select --help`` for more information.


.. _mkprof-tutorial:

mkprof
''''''

Rather than selecting data to send to stdout, you can also output a
new [incr tsdb()] profile with the :command:`mkprof` subcommand. If a
profile is given via the ``--source`` option, the relations file of
the source profile is used by default, and you may use a ``--where``
option to use TSQL_ conditions to filter the data used in creating the
new profile. Otherwise, the ``--relations`` option is required, and
the input may be a file of sentences via the ``--input`` option, or a
stream of sentences via stdin.  Sentences via file or stdin can be
prefixed with an asterisk, in which case they are considered
ungrammatical (``i-wf`` is set to ``0``). Here is an example:

.. code:: console

   $ echo -e "A dog barks.\n*Dog barks a." \
   > | delphin mkprof \
   >     --relations ~/logon/lingo/lkb/src/tsdb/skeletons/english/Relations \
   >     --skeleton
   >     newprof
   9746   bytes  relations
   67     bytes  item

Using ``--where``, sub-profiles can be created, which may be useful
for testing different parameters. For example, to create a sub-profile
with only items of less than 10 words, do this:

.. code:: console

   $ delphin mkprof --where 'i-length < 10' \
   >                --source ~/grammars/jacy/tsdb/gold/mrs/ \
   >                mrs-short
   9067   bytes  relations
   12515  bytes  item
   [...]

See ``delphin mkprof --help`` for more information.


.. _process-tutorial:

process
'''''''

PyDelphin can use ACE to process [incr tsdb()] testsuites. As with the
`art <http://sweaglesw.org/linguistics/libtsdb/art>`_ utility, the
workflow is to first create an empty testsuite (see `mkprof`_ above),
then to process that testsuite in place.

.. code:: console

   $ delphin mkprof -s erg/tsdb/gold/mrs/ mrs-parsed
    9746  bytes  relations
    10810 bytes  item
    [...]
   $ delphin process -g erg-1214-x86-64-0-9.27.dat mrs-parsed
   NOTE: parsed 107 / 107 sentences, avg 3253k, time 2.50870s

The default task is parsing, but transfer and generation are also
possible. For these, it is suggested to create a separate output
testsuite for the results, as otherwise it would overwrite the
``results`` table. Generation is activated with the ``-e`` option, and
the ``-s`` option selects the source profile.

.. code:: console

   $ delphin mkprof -s erg/tsdb/gold/mrs/ mrs-generated
    9746  bytes  relations
    10810 bytes  item
    [...]
   $ delphin process -g erg-1214-x86-64-0-9.27.dat -e -s mrs-parsed mrs-generated
   NOTE: 77 passive, 132 active edges in final generation chart; built 77 passives total. [1 results]
   NOTE: 59 passive, 139 active edges in final generation chart; built 59 passives total. [1 results]
   [...]
   NOTE: generated 440 / 445 sentences, avg 4880k, time 17.23859s
   NOTE: transfer did 212661 successful unifies and 244409 failed ones

Try `delphin process --help` for more information.

.. seealso::

  The `art <http://sweaglesw.org/linguistics/libtsdb/art>`_ utility and
  `[incr tsdb()] <http://moin.delph-in.net/ItsdbTop>`_ are other
  testsuite processors with different kinds of functionality.

.. _compare-tutorial:

compare
'''''''

The ``compare`` subcommand is a lightweight way to compare bags of MRSs,
e.g., to detect changes in a profile run with different versions of the
grammar.

.. code:: console

   $ delphin compare ~/grammars/jacy/tsdb/current/mrs/ \
   >                 ~/grammars/jacy/tsdb/gold/mrs/
   11  <1,0,1>
   21  <1,0,1>
   31  <3,0,1>
   [..]

Try ``delphin compare --help`` for more information.

.. seealso::

  The `gTest <https://github.com/goodmami/gtest>`_ application is a
  more fully-featured profile comparer, as is
  `[incr tsdb()] <http://moin.delph-in.net/ItsdbTop>`_ itself.


.. _repp-tutorial:

repp
''''

A regular expression preprocessor (REPP) can be used to tokenize input
strings.

.. code:: console

   $ delphin repp -c erg/pet/repp.set --format triple <<< "Abrams didn't chase Browne."
   (0, 6, Abrams)
   (7, 10, did)
   (10, 13, n’t)
   (14, 19, chase)
   (20, 26, Browne)
   (26, 27, .)

PyDelphin is not as fast as the C++ implementation, but its tracing
functionality can be useful for debugging.

.. code:: console

   $ delphin repp -c erg/pet/repp.set --trace --format triple <<< "Abrams didn't chase Browne."
   Applied: !^(.+)$		 \1 
   -Abrams didn't chase Browne.
   + Abrams didn't chase Browne. 
   Applied: !'		’
   - Abrams didn't chase Browne. 
   + Abrams didn’t chase Browne. 
   Applied: !^(.+)$		 \1 
   - Abrams didn’t chase Browne. 
   +  Abrams didn’t chase Browne.  
   Applied: !  +		 
   -  Abrams didn’t chase Browne.  
   + Abrams didn’t chase Browne. 
   Applied: !([^ ])(\.) ([])}⌊⌋”"’'… ]*)$		\1 \2 \3
   - Abrams didn’t chase Browne. 
   + Abrams didn’t chase Browne . 
   Applied: !([^ ])([nN])[’'‘]([tT]) 		\1 \2’\3 
   - Abrams didn’t chase Browne . 
   + Abrams did n’t chase Browne . 
   Done: Abrams did n’t chase Browne . 
   (0, 6, Abrams)
   (7, 10, did)
   (10, 13, n’t)
   (14, 19, chase)
   (20, 26, Browne)
   (26, 27, .)

When outputting to a TTY, the output will be colored in the "diff"
format. The ``--verbose`` (or ``-v``) option is also useful. With
``-v``, warnings about invalid REPP patterns will be shown; with
``-vv``, information about each REPP module called and the final
pre-tokenization alignments are shown; and with ``-vvv``, debug lines
will be shown with every rule attempted.

Try ``delphin repp --help`` for more information.

.. seealso::

   - The C++ REPP implementation:
     http://moin.delph-in.net/ReppTop#REPP_in_PET_and_Stand-Alone
