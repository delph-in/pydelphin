
delphin.predicate
=================

.. automodule:: delphin.predicate

   Semantic predicates are atomic symbols representing semantic
   entities or constructions. For example, in the `English Resource
   Grammar <http://www.delph-in.net/erg/>`_, `_mouse_n_1` is the
   predicate for the word *mouse*, but it is underspecified for
   lexical semantics---it could be an animal, a computer's pointing
   device, or something else. Another example from the ERG is
   `compound`, which is used to link two compounded nouns, such as for
   *mouse pad*.

   There are two main categories of predicates: **abstract** and
   **surface**.  In form, abstract predicates do not begin with an
   underscore and in usage they often correspond to semantic
   constructions that are not represented by a token in the input,
   such as the `compound` example above. Surface predicates, in
   contrast, are the semantic representation of surface (i.e.,
   lexical) tokens, such as the `_mouse_n_1` example above. In form,
   they must always begin with a single underscore, and have two or
   three components: lemma, part-of-speech, and (optionally) sense.

   .. seealso::
      - The DELPH-IN wiki about predicates:
	http://moin.delph-in.net/PredicateRfc

   In DELPH-IN there is the concept of "real predicates" which are
   surface predicates decomposed into their lemma, part-of-speech, and
   sense, but in PyDelphin (as of `v1.0.0`_) predicates are always
   simple strings. However, this module has functions for composing
   and decomposing predicates from/to their components (the
   :func:`create` and :func:`split` functions, respectively). In
   addition, there are functions to normalize (:func:`normalize`) and
   validate (:func:`is_valid`, :func:`is_surface`,
   :func:`is_abstract`) predicate symbols.

   .. _v1.0.0: https://github.com/delph-in/pydelphin/releases/tag/v1.0.0


   Module Functions
   ----------------

   .. autofunction:: split
   .. autofunction:: create
   .. autofunction:: normalize
   .. autofunction:: is_valid
   .. autofunction:: is_surface
   .. autofunction:: is_abstract


   Exceptions
   ----------

   .. autoexception:: PredicateError
      :show-inheritance:
