
delphin.tfs
===========

.. automodule:: delphin.tfs

   This module defines the :class:`FeatureStructure` and
   :class:`TypedFeatureStructure` classes, which model an attribute
   value matrix (AVM), with the latter including an associated
   type. They allow feature access through TDL-style dot notation
   regular dictionary keys.

   In addition, the :class:`TypeHierarchy` class implements a
   multiple-inheritance hierarchy with checks for type subsumption and
   compatibility.


   Classes
   -------

   .. autoclass:: FeatureStructure
      :members:

   .. autoclass:: TypedFeatureStructure
      :show-inheritance:
      :members:

   .. autoclass:: TypeHierarchy
      :show-inheritance:
      :members:
      :inherited-members:
