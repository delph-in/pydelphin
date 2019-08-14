
delphin.itsdb
=============

.. seealso::

  See :doc:`../guides/itsdb` for a more user-friendly introduction


.. automodule:: delphin.itsdb


   .. note::

      This module implements high-level structures and operations on
      top of TSDB test suites. For the basic, low-level functionality,
      see :mod:`delphin.tsdb`. For complex queries of the databases,
      see :mod:`delphin.tsql`.

   [incr tsdb()] is a tool built on top of TSDB databases for the
   purpose of profiling and comparing grammar versions using test
   suites. This module is named after that tool as it also builds
   higher-level operations on top of TSDB test suites but it has a
   much narrower scope. The aim of this module is to assist users with
   creating, processing, or manipulating test suites.

   The typical test suite contains these files::

     testsuite/
       analysis  fold             item-set   parse       relations  run    tree
       decision  item             output     phenomenon  result     score  update
       edge      item-phenomenon  parameter  preference  rule       set


Test Suite Classes
------------------

PyDelphin has three classes for working with [incr tsdb()] test suite
databases:

- :class:`TestSuite`
- :class:`Table`
- :class:`Row`

.. autoclass:: TestSuite
   :show-inheritance:
   :members:
   :inherited-members:

.. autoclass:: Table
   :show-inheritance:
   :members:
   :inherited-members:

.. autoclass:: Row
  :members:


Processing Test Suites
----------------------

The :meth:`TestSuite.process` method takes an optional
:class:`FieldMapper` object which manages the mapping of data in
:class:`~delphin.interface.Response` objects from a
:class:`~delphin.interface.Processor` to the tables and columns of a
test suite. In most cases the user will not need to customize or
instantiate these objects as the default works with standard [incr
tsdb()] schemas, but :class:`FieldMapper` can be subclassed in order
to handle non-standard schemas, e.g., for machine translation
workflows.

.. autoclass:: FieldMapper

   .. automethod:: map
   .. automethod:: cleanup
   .. automethod:: collect

Utility Functions
-----------------

.. autofunction:: match_rows

Exceptions
----------

.. autoexception:: ITSDBError
   :show-inheritance:
