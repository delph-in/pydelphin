
delphin.hierarchy
=================

.. automodule:: delphin.hierarchy

   This module defines the :class:`MultiHierarchy` class for
   multiply-inheriting hierarchies. This class manages the insertion
   of new nodes into the hierarchy via the class constructor or the
   :meth:`MultiHierarchy.update` method, normalizing node identifiers
   (if a suitable normalization function is provided at
   instantiation), and inserting nodes in the appropriate order. It
   checks for some kinds of ill-formed hierarchies, such as cycles and
   redundant parentage and provides methods for testing for node
   compatibility and subsumption. For convenience, arbitrary data may
   be associated with node identifiers.

   While the class may be used directly, it is mainly used to support
   the :class:`~delphin.tfs.TypeHierarchy` class and the predicate,
   property, and variable hierarchies of :class:`~delphin.semi.SemI`
   instances.

   Classes
   -------

   .. autoclass:: MultiHierarchy
      :members:

   Exceptions
   ----------

   .. autoexception:: HierarchyError
      :show-inheritance:
