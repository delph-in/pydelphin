
delphin.lnk
=================

.. automodule:: delphin.lnk

   In DELPH-IN semantic representations, entities are aligned to the
   input surface string is through the so-called "lnk" (pronounced
   "link") values. There are four types of lnk values which align to the
   surface in different ways:

   * Character spans (also called "characterization pointers"); e.g.,
     `<0:4>`

   * Token indices; e.g., `<0 1 3>`

   * Chart vertex spans; e.g., `<0#2>`

   * Edge identifier; e.g., `<@42>`

   The latter two are unlikely to be encountered by users. Chart vertices
   were used by the `PET`_ parser but are now essentially deprecated and
   edge identifiers are only used internally in the `LKB`_ for
   generation. I will therefore focus on the first two kinds.

   .. _`PET`: http://moin.delph-in.net/PetTop
   .. _`LKB`: http://moin.delph-in.net/LkbTop

   Character spans (sometimes called "characterization pointers") are by
   far the most commonly used type---possibly even the only type most
   users will encounter. These spans indicate the positions *between*
   characters in the input string that correspond to a semantic entity,
   similar to how Python and Perl do string indexing. For example,
   `<0:4>` would capture the first through fourth characters---a span
   that would correspond to the first word in a sentence like "Dogs
   bark". These spans assume the input is a flat, or linear, string and
   can only select contiguous chunks. Character spans are used by REPP
   (the Regular Expression PreProcessor; see :mod:`delphin.repp`) to
   track the surface alignment prior to string changes introduced by
   tokenization.

   Token indices select input tokens rather than characters. This method,
   though not widely used, is more suitable for input sources that are
   not flat strings (e.g., a lattice of automatic speech recognition
   (ASR) hypotheses), or where non-contiguous sequences are needed (e.g.,
   from input containing markup or other noise).

   .. note::

     Much of this background is from comments in the `LKB`_ source code:
     See: http://svn.emmtee.net/trunk/lingo/lkb/src/mrs/lnk.lisp

   Support for lnk values in PyDelphin is rather simple. The :class:`Lnk`
   class is able to parse lnk strings and model the contents for
   serialization of semantic representations. In addition, semantic
   entities such as DMRS :class:`Nodes <delphin.dmrs.Node>` and MRS
   :class:`EPs <delphin.mrs.EP>` have `cfrom` and `cto` attributes which
   are the start and end pointers for character spans (defaulting to `-1`
   if a character span is not specified for the entity).


   Classes
   -------

   .. autoclass:: Lnk
      :members:
   .. autoclass:: LnkMixin
      :members:


   Exceptions
   ----------

   .. autoexception:: LnkError
      :show-inheritance:
