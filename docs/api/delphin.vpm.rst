
delphin.vpm
===========

.. automodule:: delphin.vpm

   Variable property mappings (VPMs) convert grammar-internal
   variables (e.g. `event5`) to the grammar-external form (e.g. `e5`),
   and also map variable properties (e.g. `PNG: 1pl` might map to
   `PERS: 1` and `NUM: pl`).

   .. seealso::
      - Wiki about VPM: http://moin.delph-in.net/RmrsVpm


   Module functions
   ----------------

   .. autofunction:: load

   Classes
   -------

   .. autoclass:: VPM
      :members:

   Exceptions
   ----------

   .. autoexception:: VPMSyntaxError
      :show-inheritance:
