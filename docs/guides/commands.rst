
PyDelphin at the Command Line
=============================

While PyDelphin primarily exists as a library to be used by other
software, for convenience it also provides a top-level script for some
common actions. There are two ways to call this script, depending on how
you installed PyDelphin:

- `delphin.sh` - if you've downloaded the PyDelphin source
  files, this script is available in the top directory of the code
- `delphin` - if you've installed PyDelphin via
  `pip`, it is available system-wide as `delphin`
  (without the `.sh`)

For this guide, it is assumed you've installed PyDelphin via `pip` and
thus use the second form.

The `delphin` command has several subcommands, described
below.

.. seealso::

   The :mod:`delphin.commands` module provides a Python API for these
   commands.

.. _convert-tutorial:

convert
-------

The `convert` subcommand enables conversion of various \*MRS
representations. You provide `--from` and `--to` arguments to select
the representations (the default for both is `simplemrs`). Here is an
example of converting SimpleMRS to JSON-serialized DMRS:

.. code:: bash

  $ echo '[ "It rains." TOP: h0 RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ]' \
    | delphin convert --to dmrs-json
  [{"surface": "It rains.", "links": [{"to": 10000, "rargname": null, "from": 0, "post": "H"}], "nodes": [{"sortinfo": {"cvarsort": "e"}, "lnk": {"to": 8, "from": 3}, "nodeid": 10000, "predicate": "_rain_v_1"}]}]

As the default for `--from` and `--to` is `simplemrs`, it can be used
to easily "pretty-print" an MRS (if you execute this in a terminal,
you'll notice syntax highlighting as well):

.. code:: bash

  $ echo '[ "It rains." TOP: h0 RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ]' \
    | delphin convert --pretty-print
  [ "It rains."
    TOP: h0
    RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] >
    HCONS: < h0 qeq h1 > ]

Some formats are export-only, such as `dmrs-tikz`:

.. code:: bash

  $ echo '[ "It rains." TOP: h0 RELS: < [ _rain_v_1<3:8> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ]' \
    | delphin convert --to dmrs-tikz
  \documentclass{standalone}

  \usepackage{tikz-dependency}
  \usepackage{relsize}
  [...]

See `delphin convert --help` for more information.


.. _select-tutorial:

select
------

The `select` subcommand selects data from an [incr tsdb()] profile
using TSQL_ queries. For example, if you want to get the `i-id` and
`i-input` fields from a profile, do this:

.. _TSQL: http://moin.delph-in.net/TsqlRfc

.. code:: bash

  $ delphin select 'i-id i-input from item' ~/grammars/jacy/tsdb/gold/mrs/
  11@雨 が 降っ た ．
  21@太郎 が 吠え た ．
  [..]


In many cases, the ``from`` clause of the query is not necessary, and
the appropriate tables will be selected automatically.  Fields from
multiple tables can be used and the tables containing them will be
automatically :func:`joined <delphin.itsdb.join>`:

.. code:: bash

  $ delphin select 'i-id mrs' ~/grammars/jacy/tsdb/gold/mrs/
  11@[ LTOP: h1 INDEX: e2 ... ]
  [..]

The results can be filtered by providing ``where`` clauses:

.. code:: bash

  $ delphin select 'i-id i-input where i-input ~ "雨"' ~/grammars/jacy/tsdb/gold/mrs/
  11@雨 が 降っ た ．
  71@太郎 が タバコ を 次郎 に 雨 が 降る と 賭け た ．
  81@太郎 が 雨 が 降っ た こと を 知っ て い た ．

See `delphin select --help` for more information.


.. _mkprof-tutorial:

mkprof
------

Rather than selecting data to send to stdout, you can also output a
new [incr tsdb()] profile with the `mkprof` subcommand. If a profile
is given via the `--source` option, the relations file of the source
profile is used by default, and you may use a ``--where`` option to
use TSQL_ conditions to filter the data used in creating the new
profile. Otherwise, the `--relations` option is required, and the
input may be a file of sentences via the `--input` option, or a stream
of sentences via stdin.  Sentences via file or stdin can be prefixed
with an asterisk, in which case they are considered ungrammatical
(`i-wf` is set to `0`). Here is an example:

.. code:: bash

  $ echo -e "A dog barks.\n*Dog barks a." \
    | delphin mkprof \
        --relations ~/logon/lingo/lkb/src/tsdb/skeletons/english/Relations \
        newprof
  9746   bytes  relations
  67     bytes  item

Using ``--where``, sub-profiles can be created, which may be useful
for testing different parameters. For example, to create a sub-profile
with only items of less than 10 words, do this:

.. code:: bash

  $ delphin mkprof --where 'i-length < 10' \
                   --source ~/grammars/jacy/tsdb/gold/mrs/ \
                   mrs-short
  9067   bytes  relations
  12515  bytes  item

See `delphin mkprof --help` for more information.


.. _process-tutorial:

process
-------

PyDelphin can use ACE to process [incr tsdb()] testsuites. As with the
`art <http://sweaglesw.org/linguistics/libtsdb/art>`_ utility, the
workflow is to first create an empty testsuite (see `mkprof`_ above),
then to process that testsuite in place.

.. code:: bash

  $ delphin mkprof -s erg/tsdb/gold/mrs/ mrs-parsed
   9746  bytes  relations
   10810 bytes  item
   [...]
  $ delphin process -g erg-1214-x86-64-0-9.27.dat mrs-parsed
  NOTE: parsed 107 / 107 sentences, avg 3253k, time 2.50870s

The default task is parsing, but transfer and generation are also
possible. For these, it is suggested to create a separate output
testsuite for the results, as otherwise it would overwrite the
`results` table. Generation is activated with the `-e` option,
and the `-s` option selects the source profile.

.. code:: bash

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

See `delphin process --help` for more information.

.. seealso::

  The `art <http://sweaglesw.org/linguistics/libtsdb/art>`_ utility and
  `[incr tsdb()] <http://moin.delph-in.net/ItsdbTop>`_ are other
  testsuite processors with different kinds of functionality.

.. _compare-tutorial:

compare
-------

The `compare` subcommand is a lightweight way to compare bags of MRSs,
e.g., to detect changes in a profile run with different versions of the
grammar.

.. code:: bash

  $ delphin compare ~/grammars/jacy/tsdb/current/mrs/ \
                    ~/grammars/jacy/tsdb/gold/mrs/
  11  <1,0,1>
  21  <1,0,1>
  31  <3,0,1>
  [..]

See `delphin compare --help` for more information.

.. seealso::

  The `gTest <https://github.com/goodmami/gtest>`_ application is a
  more fully-featured profile comparer, as is
  `[incr tsdb()] <http://moin.delph-in.net/ItsdbTop>`_ itself.


.. _repp-tutorial:

repp
----

A regular expression preprocessor (REPP) can be used to tokenize input
strings.

.. code:: bash

  $ delphin repp -c erg/pet/repp.set --format triple <<< "Abrams didn't chase Browne."
  (0, 6, Abrams)
  (7, 10, did)
  (10, 13, n’t)
  (14, 19, chase)
  (20, 26, Browne)
  (26, 27, .)

PyDelphin is not as fast as the C++ implementation, but its tracing
functionality can be useful for debugging.

.. code:: bash

  $ delphin repp -c erg/pet/repp.set --trace <<< "Abrams didn't chase Browne."
  Applied:!^(.+)$		 \1 
     In:Abrams didn't chase Browne.
    Out: Abrams didn't chase Browne. 
  Applied:!'		’
     In: Abrams didn't chase Browne. 
    Out: Abrams didn’t chase Browne. 
  Applied:Internal group #1
     In: Abrams didn't chase Browne. 
    Out: Abrams didn’t chase Browne. 
  Applied:Internal group #1
     In: Abrams didn't chase Browne. 
    Out: Abrams didn’t chase Browne. 
  Applied:Module quotes
     In: Abrams didn't chase Browne. 
    Out: Abrams didn’t chase Browne. 
  Applied:!^(.+)$		 \1 
     In: Abrams didn’t chase Browne. 
    Out:  Abrams didn’t chase Browne.  
  Applied:!  +		 
     In:  Abrams didn’t chase Browne.  
    Out: Abrams didn’t chase Browne. 
  Applied:!([^ ])(\.) ([])}”"’'… ]*)$		\1 \2 \3
     In: Abrams didn’t chase Browne. 
    Out: Abrams didn’t chase Browne . 
  Applied:Internal group #1
     In: Abrams didn’t chase Browne. 
    Out: Abrams didn’t chase Browne . 
  Applied:Internal group #1
     In: Abrams didn’t chase Browne. 
    Out: Abrams didn’t chase Browne . 
  Applied:!([^ ])([nN])[’']([tT]) 		\1 \2’\3 
     In: Abrams didn’t chase Browne . 
    Out: Abrams did n’t chase Browne . 
  Applied:Module tokenizer
     In:Abrams didn't chase Browne.
    Out: Abrams did n’t chase Browne . 
  Done: Abrams did n’t chase Browne . 

See `delphin repp --help` for more information.

.. seealso::

  - The C++ REPP implementation:
    http://moin.delph-in.net/ReppTop#REPP_in_PET_and_Stand-Alone
