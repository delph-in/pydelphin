
Working with [incr tsdb()] Test Suites
======================================

[incr tsdb()] is the canonical software for managing **test
suites**---collections of test items for judging the performance of an
implemented grammar---within DELPH-IN. While the original purpose of
test suites is to aid in grammar development, they are also useful
more generally for batch processing. PyDelphin has good support for a
range of [incr tsdb()] functionality. Low-level operations on test
suite databases are defined in :mod:`delphin.tsdb` while
:mod:`delphin.itsdb` builds on top of :mod:`delphin.tsdb` to provide a
more user-friendly API and support for processing (e.g, parsing) test
suites.

There are several words in use to describe test suites:

:skeleton:

  a test suite containing only input items and static annotations, such
  as for indicating grammaticality or listing exemplified phenomena,
  ready to be processed

:profile:

  a test suite augmented with analyses from a grammar; useful for
  inspecting the grammar's competence and performance, or for building
  treebanks

:test suite:

  a general term for both skeletons and profiles

Also note that :mod:`delphin.itsdb` uses SQL-like terminology for
database entities while :mod:`delphin.tsdb` usually uses the older
relational database terms (to be consistent with [incr tsdb()]):

===========  ============  =================  ==========================================
`tsdb` term  `itsdb` term  Casual term        Examples
===========  ============  =================  ==========================================
Database     Test Suite    "profile"          `tsdb/gold/mrs/`, `tsdb/skeletons/mrs/`
"            Profile       "profile"          `tsdb/gold/mrs/`
"            Skeleton      "skeleton"         `tsdb/skeletons/mrs/`
Schema       Schema        "relations file"   `tsdb/gold/mrs/relations`
Field        Field         "field"            `i-input :string` (in a schema)
Relation     Table         "item file", etc.  `tsdb/gold/mrs/item`
Record       Row           "line"             `11@unknown@formal@none@1@S@It rained.@...`
Column       Column        "field", "column"  `i-id`
===========  ============  =================  ==========================================

This guide covers the :mod:`delphin.itsdb` module and expects that
you've imported it as follows:

>>> from delphin import itsdb

.. seealso::

  - The [incr tsdb()] homepage: http://www.delph-in.net/itsdb/
  - The [incr tsdb()] wiki: http://moin.delph-in.net/ItsdbTop
  - The Wikipedia entry on database terminology:
    https://en.wikipedia.org/wiki/Relational_database#Terminology


Loading and Inspecting Test Suites
----------------------------------

Loading a test suite is as simple as creating a
:class:`~delphin.itsdb.TestSuite` object with the directory as its
argument:

>>> ts = itsdb.TestSuite('~/grammars/erg/tsdb/gold/mrs')


The :class:`~delphin.itsdb.TestSuite` instance loads the database
schema and uses it to inspect the data in tables. The schema can be
inspected via the :attr:`TestSuite.schema
<delphin.itsdb.TestSuite.schema>` attribute:

>>> list(ts.schema)
['item', 'analysis', 'phenomenon', 'parameter', 'set', 'item-phenomenon', 'item-set', 'run', 'parse', 'result', 'rule', 'output', 'edge', 'tree', 'decision', 'preference', 'update', 'fold', 'score']
>>> [field.name for field in ts.schema['phenomenon']]
['p-id', 'p-name', 'p-supertypes', 'p-presupposition', 'p-interaction', 'p-purpose', 'p-restrictions', 'p-comment', 'p-author', 'p-date']


Key lookups on the test suite return the :class:`~delphin.itsdb.Table`
whose name is the given key. Note that the table name is as it appears
in the schema and not necessarily the table's filename (e.g., in case
the table is compressed and the filename has a `.gz` extension).

>>> len(ts['item'])
107
>>> ts['item'][0]['i-input']
'It rained.'

Iterating over a table yields rows from the table. A
:class:`~delphin.itsdb.Row` object stores the raw string data
internally (accessed via :attr:`Row.data <delphin.itsdb.Row.data>`),
but upon iteration or column lookup it is cast depending on the
datatype specified in the schema.

>>> row = next(iter(ts['item']))
>>> row.data
('11', 'unknown', 'formal', 'none', '1', 'S', 'It rained.', '', '', '', '1', '2', 'Det regnet.', 'oe', '15-10-2006')
>>> tuple(row)
(11, 'unknown', 'formal', 'none', 1, 'S', 'It rained.', None, None, None, 1, 2, 'Det regnet.', 'oe', datetime.datetime(2006, 10, 15, 0, 0))
>>> row['i-input']
'It rained.'

The :meth:`Table.select <delphin.itsdb.Table.select>` method allows
for iterating over a restricted subset of columns:

>>> for row in ts['item'].select('i-id', 'i-input'):
...     print(tuple(row))
... 
(11, 'It rained.')
(21, 'Abrams barked.')
(31, 'The window opened.')
[...]


Modifying Test Suite Data
-------------------------

Test suite data can be modified or extended by interacting with the
:class:`~delphin.itsdb.Table` instance. The
:func:`~delphin.tsdb.make_record` function of :mod:`delphin.tsdb` may
be useful for creating new items, or the :meth:`Table.update
<delphin.itsdb.Table.update>` method for modifying single rows.

>>> from delphin import tsdb
>>> items = ts['item']
>>> # find the next available i-id
>>> next_i_id = items[-1]['i-id'] + 1
>>> # define the data
>>> colmap = {'i-id': next_i_id, 'i-input': '...'}
>>> # add a new row
>>> items.append(tsdb.make_record(colmap, items.fields))
>>> # oops, forgot a field; reassign that last row
>>> colmap['i-wf'] = 0
>>> items[-1] = tsdb.make_record(colmap, items.fields))
>>> # oops it should be 1, just fix that one field
>>> items.update(-1, {'i-wf': 1})
>>> # write to disk
>>> ts.commit()


TSQL Queries Over Test Suites
-----------------------------

Sometimes the desired fields exist in different tables, such as when
one wants to pair an input item identifier with its results---a
one-to-many mapping. In these cases, the :mod:`delphin.tsql` module
can help.

>>> from delphin import tsql
>>> for row in tsql.select('i-id mrs', ts):
...     print(tuple(row))
... 
(11, '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ _rain_v_1<3:10> LBL: h1 ARG0: e2 ] > HCONS: < h0 qeq h1 > ICONS: < > ]')
(21, '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ proper_q<0:6> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ named<0:6> LBL: h7 CARG: "Abrams" ARG0: x3 ]  [ _bark_v_1<7:14> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ICONS: < > ]')
(31, '[ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ] RELS: < [ _the_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]  [ _window_n_1<4:10> LBL: h7 ARG0: x3 ]  [ _open_v_1<11:18> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ICONS: < > ]')
[...]

.. seealso::

   - :mod:`delphin.tsql` module
   - The Test Suite Query Language RFC wiki page: http://moin.delph-in.net/TsqlRfc
   

Writing Test Suites to Disk
---------------------------

When modifying test suites as described above, the
:meth:`TestSuite.commit <delphin.itsdb.TestSuite.commit>` method is how
the changes get written to disk. This is similar to how relational
databases perform "transactions", but currently PyDelphin does not
ensure consistency in the same way.

For more control over how data gets written to disk, see the
:mod:`delphin.tsdb` module's :func:`~delphin.tsdb.write` and
:func:`~delphin.tsdb.write_database` functions.

.. seealso::

  The :ref:`mkprof-tutorial` command is a more versatile method of
  creating test suites at the command line.


Processing Test Suites with ACE
-------------------------------

PyDelphin has the ability to process test suites using `ACE
<http://sweaglesw.org/linguistics/ace>`_, similar to the `art
<http://sweaglesw.org/linguistics/libtsdb/art>`_ utility and `[incr
tsdb()] <http://www.delph-in.net/itsdb/>`_ itself. The simplest method
is to pass in a running :class:`~delphin.ace.ACEProcess` instance to
:meth:`TestSuite.process <delphin.itsdb.TestSuite.process>`\ ---the
:class:`~delphin.itsdb.TestSuite` class will determine if the
processor is for parsing, transfer, or generation (using the
:attr:`ACEProcessor.task <delphin.ace.ACEProcess.task>` attribute)
and select the appropriate inputs from the test suite.

>>> from delphin import ace
>>> ts = itsdb.TestSuite('~/grammars/INDRA/tsdb/skeletons/matrix')
>>> with ace.ACEParser('~/grammars/INDRA/indra.dat') as cpu:
...     ts.process(cpu)
... 
NOTE: parsed 2 / 3 sentences, avg 887k, time 0.04736s

By default the processed data will be written to disk as it is
processed so the in-memory :class:`~delphin.itsdb.TestSuite` object
doesn't get too large. The `buffer_size` parameter of
:meth:`TestSuite.process <delphin.itsdb.TestSuite.process>` can be
used to write to disk more or less frequently or not at all.

When doing generation or transfer the input to the processor is in the
table that will be overwritten. To avoid loss of data, the `source`
parameter takes another :class:`~delphin.itsdb.TestSuite` instance
that provides the inputs. The :func:`delphin.commands.mkprof` function
is useful for creating an empty test suite for storing the results,
but note that it expects the test suite paths instead of
:class:`~delphin.itsdb.TestSuite` instances.

>>> from delphin import commands
>>> src_path = '~/grammars/jacy/tsdb/current/mrs'
>>> tgt_path = '~/grammars/jacy/tsdb/current/mrs-gen'
>>> commands.mkprof(tgt_path, source=src_path)
    9067 bytes	relations
   15573 bytes	item
       0 bytes	analysis
[...]
>>> src_ts = itsdb.TestSuite(src_path)
>>> tgt_ts = itsdb.TestSuite(tgt_path)
>>> with ace.ACEGenerator('~/grammars/jacy/jacy-0.9.30.dat') as cpu:
...     tgt_ts.process(cpu, source=src_ts)
... 
NOTE: 75 passive, 361 active edges in final generation chart; built 89 passives total. [1 results]
NOTE: 35 passive, 210 active edges in final generation chart; built 37 passives total. [1 results]
[...]

PyDelphin also has the ability to do `full-forest
<http://moin.delph-in.net/FftbTop>`_ parsing. In this mode, results
(with derivation trees, MRSs, etc.) do not get enumerated in the
profile but the edges of analyses are stored instead. The results of
parsing in this mode can be used for full-forest treebanking.

>>> with ace.ACEParser('~/grammars/erg.dat', full_forest=True) as cpu:
...     ts.process(cpu)


Troubleshooting
---------------

``TSDBWarning: Invalid date field``

  This warning occurs when PyDelphin tries to cast a value with the
  ``:date`` datatype when the raw value is not an acceptable date
  format (see :func:`delphin.tsdb.cast` for an
  explanation). Practically this means that the date will not be
  usable for things like TSQL conditions, but also note that it can
  cause data loss when writing a profile containing invalid dates to
  disk as PyDelphin will not write invalid data. Low-level operations
  that do not cast the value, such as from the :mod:`delphin.tsdb`
  module, may be able to write the raw string without data loss, but
  it is better to just fix the invalid dates.
