
delphin.tsdb
============

.. automodule:: delphin.tsdb

   Module Constants
   ----------------

   .. data:: SCHEMA_FILENAME

      `relations` -- The filename for the schema.

   .. data:: FIELD_DELIMITER

      `@` -- The character used to delimit fields (or columns) in a table.

   .. data:: TSDB_CORE_FILES

      The list of files used in "skeletons". Includes::

	item
	analysis
	phenomenon
	parameter
	set
	item-phenomenon
	item-set

   .. data:: TSDB_CODED_ATTRIBUTES

      The default values of specific fields. Includes::

	i-wf = 1
	i-difficulty = 1
	polarity = -1

      Fields without a special value given above get assigned one
      based on their datatype.


   Schemas
   -------

   TSDB databases define their schema in a file called ``relations``.
   It contains descriptions of tables and their fields (i.e.,
   columns), including the datatypes and whether a column counts as a
   "key". Key columns may be used when joining tables together. As an
   example, the first 9 lines of the ``run`` table description is as
   follows:

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

   .. seealso::

      See the `TsdbSchemaRfc <http://moin.delph-in.net/TsdbSchemaRfc>`_ wiki for a description of the format of ``relations`` files.

   In PyDelphin, TSDB schemas are represented as dictionaries of lists
   of :class:`Field` objects.

   .. autoclass:: Field
      :members:

   .. autofunction:: read_schema
   .. autofunction:: write_schema

   Table Data
   ----------

   .. autofunction:: escape
   .. autofunction:: unescape
   .. autofunction:: decode_row
   .. autofunction:: encode_row
   .. autofunction:: make_row
   .. autofunction:: cast


   File and Directory Operations
   -----------------------------

   .. autofunction:: is_database_directory
   .. autofunction:: table_path
   .. autofunction:: open_table
   .. autofunction:: write_table


   Basic Database and Table Classes
   --------------------------------

   .. autoclass:: Database
      :members:

   .. autoclass:: Table
      :members:


   Exceptions
   ----------

   .. autoexception:: TSDBSchemaError
      :show-inheritance:

   .. autoexception:: TSDBError
      :show-inheritance:
