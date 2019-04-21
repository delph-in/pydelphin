
delphin.dmrs
============

.. automodule:: delphin.dmrs

   Module Constants
   ----------------

   .. data:: RESTRICTION_ROLE

      The `RSTR` role used in links to select the restriction of a
      quantifier.

   .. data:: EQ_POST

      The `EQ` post-slash label on links that indicates the endpoints
      of a link share a scope.

   .. data:: NEQ_POST

      The `NEQ` post-slash label on links that indicates the endpoints
      of a link do not share a scope.

   .. data:: HEQ_POST

      The `HEQ` post-slash label on links that indicates the
      :data:`~Link.start` node of a link immediately outscopes the
      :data:`~Link.end` node.

   .. data:: H_POST

      The `H` post-slash label on links that indicates the
      :data:`~Link.start` node of a link is qeq to the
      :data:`~Link.end` node (i.e., :data:`~Link.start` scopes over
      :data:`~Link.end`, but not necessarily immediately).

   .. data:: CVARSORT

      The `cvarsort` dictionary key in :data:`Node.sortinfo` that
      accesses the node's :data:`~Node.type`.

   Classes
   -------

   .. autoclass:: DMRS
      :members:

   .. autoclass:: Node
      :members:

   .. autoclass:: Link
      :members:

   Exceptions
   ----------

   .. autoexception:: DMRSSyntaxError

   Serialization Formats
   ---------------------

   .. toctree::

      delphin.dmrs.dmrx.rst
      delphin.dmrs.simpledmrs.rst
