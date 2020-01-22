
delphin.tsql
============

.. seealso::

  The :ref:`select-tutorial` command is a quick way to query test
  suites with TSQL queries.

.. automodule:: delphin.tsql

   .. note::

      This module deals with queries of TSDB databases. For basic,
      low-level access to the databases, see :mod:`delphin.tsdb`. For
      high-level operations and structures on top of the databases,
      see :mod:`delphin.itsdb`.

   This module implements a subset of TSQL, namely the 'select' (or
   'retrieve') queries for extracting data from test suites. The
   general form of a select query is::

       [select] <projection> [from <relations>] [where <condition>]*

   For example, the following selects item identifiers that took more
   than half a second to parse::

       select i-id from item where total > 500

   The `select` string is necessary when querying with the generic
   :func:`query` function, but is implied and thus disallowed when
   using the :func:`select` function.

   The `<projection>` is a list of space-separated field names (e.g.,
   `i-id i-input mrs`), or the special string `*` which selects all
   columns from the joined relations.

   The optional `from` clause provides a list of relation names (e.g.,
   `item parse result`) that are joined on shared keys. The `from`
   clause is required when `*` is used for the projection, but it can
   also be used to select columns from non-standard relations (e.g.,
   `i-id from output`). Alternatively, qualified names (e.g.,
   `item.i-id`) can specify both the column and the relation at the
   same time.

   The `where` clause provide conditions for filtering the list of
   results. Conditions are binary operations that take a column or
   data specifier on the left side and an integer (e.g., `10`), a date
   (e.g., `2018-10-07`), or a string (e.g., `"sleep"`) on the right
   side of the operator. The allowed conditions are:

   ================  ======================================
   Condition         Form
   ================  ======================================
   Regex match       ``<field> ~ "regex"``
   Regex fail        ``<field> !~ "regex"``
   Equality          ``<field> = (integer|date|"string")``
   Inequality        ``<field> != (integer|date|"string")``
   Less-than         ``<field> < (integer|date)``
   Less-or-equal     ``<field> <= (integer|date)``
   Greater-than      ``<field> > (integer|date)``
   Greater-or-equal  ``<field> >= (integer|date)``
   ================  ======================================

   Boolean operators can be used to join multiple conditions or for
   negation:

   ===========  =====================================
   Operation    Form
   ===========  =====================================
   Disjunction  ``X | Y``, ``X || Y``, or ``X or Y``
   Conjunction  ``X & Y``, ``X && Y``, or ``X and Y``
   Negation     ``!X`` or ``not X``
   ===========  =====================================

   Normally, disjunction scopes over conjunction, but parentheses may
   be used to group clauses, so the following are equivalent::

       ... where i-id = 10 or i-id = 20 and i-input ~ "[Dd]og"
       ... where i-id = 10 or (i-id = 20 and i-input ~ "[Dd]og")

   Multiple `where` clauses may also be used as a conjunction that
   scopes over disjunction, so the following are equivalent::

       ... where (i-id = 10 or i-id = 20) and i-input ~ "[Dd]og"
       ... where i-id = 10 or i-id = 20 where i-input ~ "[Dd]og"

   This facilitates query construction, where a user may want to apply
   additional global constraints by appending new conditions to the
   query string.

   PyDelphin has several differences to standard TSQL:

   * `select *` requires a `from` clause
   * `select * from item result` does not also include columns from
     the intervening `parse` relation
   * `select i-input from result` returns a matching `i-input` for
     every row in `result`, rather than only the unique rows

   PyDelphin also adds some features to standard TSQL:

   * qualified column names (e.g., `item.i-id`)
   * multiple `where` clauses (as described above)


   Module Functions
   ----------------

   .. autofunction:: inspect_query
   .. autofunction:: query
   .. autofunction:: select

   Exceptions
   ----------

   .. autoexception:: TSQLSyntaxError
      :show-inheritance:

   .. autoexception:: TSQLError
      :show-inheritance:
