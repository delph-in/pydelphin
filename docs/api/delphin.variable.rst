
delphin.variable
================

.. automodule:: delphin.variable

   Module Constants
   ----------------

   .. data:: UNSPECIFIC

      `u` -- The unspecific (or unbound) top-level variable type.

   .. data:: INDIVIDUAL

      `i` -- The variable type that generalizes over eventualities and
      instances.

   .. data:: INSTANCE_OR_HANDLE

      `p` -- The variable type that generalizes over instances and
      handles.

   .. data:: EVENTUALITY

      `e` -- The variable type for events and other eventualities
      (adjectives, adverbs, prepositions, etc.).

   .. data:: INSTANCE

      `x` -- The variable type for instances and nominal things.

   .. data:: HANDLE

      `h` -- The variable type for scope handles and labels.

   Module Functions
   ----------------

   .. autofunction:: split
   .. autofunction:: sort
   .. autofunction:: id
   .. autofunction:: is_valid

   Classes
   -------

   .. autoclass:: VariableFactory
      :members:
