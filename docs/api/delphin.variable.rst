
delphin.variable
================

.. automodule:: delphin.variable

   This module contains functions to inspect the type and identifier
   of variables (:func:`split`, :func:`type`, :func:`id`) and check if
   a variable string is well-formed (:func:`is_valid`). It
   additionally has constants for the standard variable types:
   :data:`UNSPECIFIC`, :data:`INDIVIDUAL`, :data:`INSTANCE_OR_HANDLE`,
   :data:`EVENTUALITY`, :data:`INSTANCE`, and :data:`HANDLE`. Finally,
   the :class:`VariableFactory` class may be useful for tasks like
   DMRS to MRS conversion for managing the creation of new variables.

   Variables in MRS
   ----------------

   Variables are a concept in Minimal Recursion Semantics coming from
   formal semantics. Consider this logical form for a sentence like
   "the dog barks"::

       ∃x(dog(x) ^ bark(x))

   Here *x* is a variable that represents an entity that has the
   properties that it is a dog and it is barking. Davidsonian
   semantics introduce variables for events as well::

       ∃e∃x(dog(x) ^ bark(e, x))

   MRS uses variables in a similar way to Davidsonian semantics,
   except that events are not explicitly quantified. That might look
   like the following (if we ignore quantifier scope
   underspecification)::

       the(x4) [dog(x4)] {bark(e2, x4)}

   "Variables" are also used for scope handles and labels, as in this
   minor modification that indicates the scope handles::

       h3:the(x4) [h6:dog(x4)] {h1:bark(e2, x4)}

   There is some confusion of terminology here. Sometimes "variable"
   is contrasted with "handle" to mean an instance (`x`) or
   eventuality (`e`) variable, but in this module "variable" means the
   identifiers used for instances, eventualities, handles, and their
   supertypes.

   The form of MRS variables is the concatenation of a variable *type*
   (also called a *sort*) with a variable *id*. For example, the
   variable type `e` and id `2` form the variable `e2`. Generally in
   MRS the variable ids, regardless of the type, are unique, so for
   instance one would not see `x2` and `e2` in the same structure.

   The variable types are arranged in a hierarchy. While the most
   accurate variable type hierarchy for a particular grammar is
   obtained via its SEM-I (see :mod:`delphin.semi`), in practice the
   standard hierarchy given below is used by all DELPH-IN
   grammars. The hierarchy in TDL would look like this (with an ASCII
   rendering in comments on the right):

   .. code-block:: tdl

      u := *top*.  ;     u
      i := u.      ;    / \
      p := u.      ;   i   p
      e := i.      ;  / \ / \
      x := i & p.  ; e   x   h
      h := p.

   In PyDelphin the equivalent hierarchy could be created as follows
   with a :class:`delphin.hierarchy.MultiHierarchy`:

   >>> from delphin import hierarchy
   >>> h = hierarchy.MultiHierarchy(
   ...     '*top*',
   ...     {'u': '*top*',
   ...      'i': 'u',
   ...      'p': 'u',
   ...      'e': 'i',
   ...      'x': 'i p',
   ...      'h': 'p'}
   ... )


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
   .. autofunction:: type
   .. autofunction:: sort
   .. autofunction:: id
   .. autofunction:: is_valid

   Classes
   -------

   .. autoclass:: VariableFactory
      :members:
