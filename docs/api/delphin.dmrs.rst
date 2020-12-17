
delphin.dmrs
============

.. automodule:: delphin.dmrs

   Serialization Formats
   ---------------------

   .. toctree::
      :maxdepth: 1

      delphin.codecs.dmrsjson.rst
      delphin.codecs.dmrspenman.rst
      delphin.codecs.dmrx.rst
      delphin.codecs.simpledmrs.rst

   Module Constants
   ----------------

   .. data:: FIRST_NODE_ID

      The node identifier `10000` which is conventionally the first
      identifier used in a DMRS structure. This constant is mainly
      used for DMRS conversion or serialization.

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
      :show-inheritance:
      :members:

   .. autoclass:: Node
      :show-inheritance:
      :members:

   .. autoclass:: Link
      :show-inheritance:
      :members:

   Module Functions
   ----------------

   .. autofunction:: from_mrs

   Exceptions
   ----------

   .. autoexception:: DMRSSyntaxError
      :show-inheritance:

   .. autoexception:: DMRSWarning
      :show-inheritance:
