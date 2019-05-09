
Working with [incr tsdb()] Testsuites
=====================================

[incr tsdb()] is the canonical software for managing
**testsuites**---collections of test items for judging the performance
of an implemented grammar---within DELPH-IN. While the original
purpose of testsuites is to aid in grammar development, they are also
useful more generally for batch processing. PyDelphin has good support
for a range of [incr tsdb()] functionality.

There are several words in use to describe testsuites:

:skeleton:

  a testsuite containing only input items and static annotations, such
  as for indicating grammaticality or listing exemplified phenomena,
  ready to be processed

:profile:

  a testsuite augmented with analyses from a grammar; useful for
  inspecting the grammar's competence and performance, or for building
  treebanks

:testsuite:

  a general term for both skeletons and profiles


For this tutorial, it is assumed you've imported the
:mod:`delphin.itsdb` module as follows:

>>> from delphin import itsdb


.. seealso::

  - The [incr tsdb()] homepage: http://www.delph-in.net/itsdb/
  - The [incr tsdb()] wiki: http://moin.delph-in.net/ItsdbTop


Loading and Inspecting Testsuites
---------------------------------

Loading a testsuite is as simple as creating a
:class:`~delphin.itsdb.TestSuite` object with the directory as its
argument:

>>> ts = itsdb.TestSuite('erg/tsdb/gold/mrs')


The `TestSuite` object loads both the relations file (i.e., the
database schema) and the data tables themselves. The relations can be
inspected via the
:attr:`TestSuite.relations <delphin.itsdb.TestSuite.relations>`
attribute:

>>> ts.relations.tables
('item', 'analysis', 'phenomenon', 'parameter', 'set', 'item-phenomenon', 'item-set', 'run', 'parse', 'result', 'rule', 'output', 'edge', 'tree', 'decision', 'preference', 'update', 'fold', 'score')
>>> [field.name for field in ts.relations['phenomenon']]
['p-id', 'p-name', 'p-supertypes', 'p-presupposition', 'p-interaction', 'p-purpose', 'p-restrictions', 'p-comment', 'p-author', 'p-date']


Key lookups on the testsuite return the :class:`~delphin.itsdb.Table`
whose name is the given key. Note that the table name is as it appears
in the relations file and not the table's filename (e.g., in case the
table is compressed and the filename has a `.gz` extension).

>>> len(ts['item'])
107
>>> ts['item'][0]['i-input']
'It rained.'


The :meth:`~delphin.itsdb.TestSuite.select` method allows for slightly
more flexible queries, such as those involving more than one field. The
method returns a Python generator for efficient iteration, so in the
following example it needs to be cast to a list for slicing.

>>> list(ts.select('item:i-id@i-input'))[0:3]
[[11, 'It rained.'], [21, 'Abrams barked.'], [31, 'The window opened.']]


Sometimes the desired fields exist in different tables, such as when
one wants to pair an input item identifier with its results---a
one-to-many mapping. In these cases, the :func:`delphin.itsdb.join`
function is useful. It returns a new :class:`~delphin.itsdb.Table` with
the joined data, and the field names are prefixed with their source
table names.

>>> joined = itsdb.join(ts['parse'], ts['result'])
>>> next(joined.select('parse:i-id@result:mrs'))
[11, '[ TOP: h1 INDEX: e3 [ e SF: PROP TENSE: PAST MOOD: INDICATIVE PROG: - PERF: - ] RELS: < [ _rain_v_1<3:10> LBL: h2 ARG0: e3 ] > HCONS: < h1 qeq h2 > ]']

.. seealso::

   The :mod:`delphin.tsql` module provides support for TSQL queries
   over test suites which are much more flexible and powerful than the
   :meth:`TestSuite.select <delphin.itsdb.TestSuite.select>` method.


Writing Testsuites to Disk
--------------------------

.. seealso::

  The :ref:`mkprof-tutorial` command is a more versatile method of
  creating testsuites at the command line.

The :meth:`~delphin.itsdb.TestSuite.write` method of TestSuites is the
primary way of writing in-memory TestSuite data to disk. Its most basic
form writes all tables to the path used to load the testsuite:

>>> from delphin import itsdb
>>> ts = itsdb.TestSuite('tsdb/gold/mrs')
>>> ts.write()

This method does not work if the testsuite was created entirely
in-memory (i.e., if it has no `path`). In this case, or also in the case
where a different destination is desired, the `path` can be specified
as a parameter:

>>> ts.write(path='tsdb/current/mrs')

The first parameter to the `write()` method is a description of what to
write. It could be a single table name, a list of table names, or a
mapping from table names to lists of table records:

>>> ts.write('item')  # only write the 'item' file
>>> ts.write(['item', 'parse'])  # only write 'item' and 'parse'
>>> ts.write({'result': result_records})  # write result_records to 'result'

By default, writing a table deletes any previous contents, so the
entire file contents need to be written at once. If you want to write
results one-by-one, the `append` parameter is useful. You many need to
clear the in-memory table before appending the first time, and this can
be done by writing an empty list with `append=False`:

>>> ts.write({'result': [], append=False)  # to erase on-disk table
>>> ts.['result'][:] = []                  # to clear in-memory table
>>> for record in result_records:
...     ts.write({'result': [record]}, append=True)

Processing Testsuites with ACE
------------------------------

PyDelphin has the ability to process testsuites using `ACE
<http://sweaglesw.org/linguistics/ace>`_, similar to the
`art <http://sweaglesw.org/linguistics/libtsdb/art>`_ utility and
`[incr tsdb()] <http://www.delph-in.net/itsdb/>`_ itself. The simplest
method is to pass in a running
:class:`~delphin.interfaces.ace.ACEProcess` instance to
:meth:`TestSuite.process <delphin.itsdb.TestSuite.process>`---the
testsuite class will determine if the processor is for parsing,
transfer, or generation (using the
:attr:`ACEProcessor.task <delphin.interfaces.ace.ACEProcessor.task>`
attribute) and select the appropriate inputs from the testsuite.

>>> from delphin import itsdb
>>> from delphin.interfaces import ace
>>> ts = itsdb.TestSuite('tsdb/skeletons/matrix')
>>> with ace.ACEParser('indra.dat') as cpu:
...     ts.process(cpu)
... 
NOTE: parsed 2 / 3 sentences, avg 887k, time 0.04736s
>>> ts.write(path='tsdb/current/matrix')

Processing a testsuite that has a path (that is, backed by files on
disk) will write the results to disk. Processing an in-memory
testsuite will store the results in-memory. For other options please
see the API documentation for :meth:`TestSuite.process
<delphin.itsdb.TestSuite.process>`, specifically the `buffer_size`
parameter. When the results are all in-memory, you can write them
to disk with TestSuite's :meth:`~delphin.itsdb.TestSuite.write` method
with the `path` parameter.

.. warning::

  PyDelphin does not prevent or warn you about overwriting skeletons or
  gold profiles, so take care when using the `write()` method without
  the `path` parameter.

If you have a testsuite object `ts` and call `ts.process()`, both the
source items and the results are stored in `ts`. For parsing this
isn't a problem because the source items and results are located in
different tables, but for transfering or generating you may want to
use the `source` parameter in order to select inputs from a separate
testsuite than the one where results will be stored:

>>> from delphin.interfaces import ace
>>> from delphin import itsdb
>>> src_ts = itsdb.TestSuite('tsdb/current/mrs')
>>> tgt_ts = itsdb.TestSuite('tsdb/current/mrs-gen')
>>> with ace.ACEGenerator('jacy-0.9.27.dat') as cpu:
...     tgt_ts.process(cpu, source=src_ts)
... 
NOTE: 75 passive, 361 active edges in final generation chart; built 89 passives total. [1 results]
NOTE: 35 passive, 210 active edges in final generation chart; built 37 passives total. [1 results]
[...]

