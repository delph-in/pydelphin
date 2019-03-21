
delphin.itsdb
=============

.. seealso::

  See :doc:`../tutorials/itsdb` for a more user-friendly introduction


.. automodule:: delphin.itsdb



Overview of [incr tsdb()] Testsuites
------------------------------------

[incr tsdb()] testsuites are directories containing a ``relations``
file (see `Relations Files and Field Descriptions`_) and a file for
each table in the database. The typical testsuite contains these files:

::

  testsuite/
    analysis  fold             item-set   parse       relations  run    tree
    decision  item             output     phenomenon  result     score  update
    edge      item-phenomenon  parameter  preference  rule       set

PyDelphin has three classes for working with [incr tsdb()] testsuite
databases:

* :class:`TestSuite` -- The entire testsuite (or directory)
* :class:`Table` -- A table (or file) in a testsuite
* :class:`Record` -- A row (or line) in a table

.. autoclass:: TestSuite
  :members:

.. autoclass:: Table

  .. automethod:: from_file
  .. automethod:: write
  .. automethod:: attach
  .. automethod:: detach
  .. automethod:: is_attached
  .. automethod:: list_changes
  .. automethod:: append
  .. automethod:: extend
  .. automethod:: select

.. autoclass:: Record
  :members:

Relations Files and Field Descriptions
--------------------------------------

A "relations file" is a required file in [incr tsdb()] testsuites that
describes the schema of the database. The file contains descriptions of
each table and each field within the table. The first 9 lines of
``run`` table description is as follows:

::

  run:
    run-id :integer :key                  # unique test run identifier
    run-comment :string                   # descriptive narrative
    platform :string                      # implementation platform (version)
    protocol :integer                     # [incr tsdb()] protocol version
    tsdb :string                          # tsdb(1) (version) used
    application :string                   # application (version) used
    environment :string                   # application-specific information
    grammar :string                       # grammar (version) used
    ...

In PyDelphin, there are three classes for modeling this information:

* :class:`Relations` -- the entire relations file schema
* :class:`Relation` -- the schema for a single table
* :class:`Field` -- a single field description

.. autoclass:: delphin.itsdb.Relations
  :members:
.. autoclass:: delphin.itsdb.Relation
  :members:
.. autoclass:: delphin.itsdb.Field
  :members:

Utility Functions
-----------------

.. autofunction:: delphin.itsdb.join
.. autofunction:: delphin.itsdb.match_rows
.. autofunction:: delphin.itsdb.select_rows
.. autofunction:: delphin.itsdb.make_row
.. autofunction:: delphin.itsdb.escape
.. autofunction:: delphin.itsdb.unescape
.. autofunction:: delphin.itsdb.decode_row
.. autofunction:: delphin.itsdb.encode_row
.. autofunction:: delphin.itsdb.get_data_specifier

Deprecated
----------

The following are remnants of the old functionality that will be
removed in a future version, but remain for now to aid in the
transition.

.. autoclass:: ItsdbProfile
  :members:
.. autoclass:: ItsdbSkeleton
  :members:
.. autofunction:: get_relations
.. autofunction:: default_value
.. autofunction:: make_skeleton
.. autofunction:: filter_rows
.. autofunction:: apply_rows
