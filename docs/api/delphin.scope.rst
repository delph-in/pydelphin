
delphin.scope
=============

.. automodule:: delphin.scope

   While the predicate-argument structure of a semantic representation
   is a directed-acyclic graph, the quantifier scope is a tree
   overlayed on the edges of that graph. In a fully scope-resolved
   structure, there is one tree spanning the entire graph, but in
   underspecified representations like MRS, there are multiple
   subtrees that span the graph nodes but are not all connected
   together. The components are then connected via qeq constraints
   which specify a partial ordering for the tree such that quantifiers
   may float in between the nodes connected by qeqs.

   Each node in the scope tree (called a *scopal position*) may
   encompass multiple nodes in the predicate-argument graph. Nodes
   that share a scopal position are said to be in a *conjunction*.

   The dependency representations EDS and DMRS develop the idea of
   scope representatives (called *representative nodes* or sometimes
   *heads*), whereby a single node is selected from a conjunction to
   represent the conjunction as a whole.

   Classes
   -------

   .. autoclass:: ScopingSemanticStructure
      :show-inheritance:
      :members:

   Module Functions
   ----------------

   .. autofunction:: conjoin
   .. autofunction:: descendants
   .. autofunction:: representatives

   Exceptions
   ----------

   .. autoexception:: ScopeError
      :show-inheritance:
