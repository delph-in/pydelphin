
delphin.variable
================

.. automodule:: delphin.variable

   Module Constants
   ----------------

   .. data:: hierarchy

      A :class:`delphin.tfs.TypeHierarchy` object containing the
      standard variable type hierarchy. While the most accurate
      variable type hierarchy for a particular grammar is obtained via
      its SEM-I (see :mod:`delphin.semi`), in practice the standard
      hierarchy given here is used by all DELPH-IN grammars. The
      hierarchy in TDL would look like this (with an ASCII rendering
      in comments on the right):

      .. code-block:: tdl

         u := *top*.  ;     u
         i := u.      ;    / \\
         p := u.      ;   i   p
         e := i.      ;  / \ / \\
         x := i & p.  ; e   x   h
         h := p.

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
