
delphin.repp
============

.. automodule:: delphin.repp

   A Regular-Expression Preprocessor [REPP]_ is a method of applying a
   system of regular expressions for transformation and tokenization
   while retaining character indices from the original input string.

   .. [REPP] Rebecca Dridan and Stephan Oepen. Tokenization: Returning
	     to a long solved problem---a survey, contrastive
	     experiment, recommendations, and toolkit. In Proceedings
	     of the 50th Annual Meeting of the Association for
	     Computational Linguistics (Volume 2: Short Papers), pages
	     378–382, Jeju Island, Korea, July 2012.  Association for
	     Computational Linguistics.  URL
	     http://www.aclweb.org/anthology/P12-2074.

.. note::

   Requires ``regex`` (https://bitbucket.org/mrabarnett/mrab-regex/),
   for advanced regular expression features such as group-local inline
   flags. Without it, PyDelphin will fall back to the :py:mod:`re`
   module in the standard library which may give some unexpected
   results. The ``regex`` library, however, will not parse unescaped
   brackets in character classes without resorting to a compatibility
   mode (see `this issue`_ for the ERG), and PyDelphin will warn if
   this happens. The ``regex`` dependency is satisfied if you install
   PyDelphin with the ``[repp]`` extra (see :doc:`../guides/setup`).

.. _this issue: https://github.com/delph-in/erg/issues/17


Module Constants
----------------

.. autodata:: DEFAULT_TOKENIZER


Classes
-------

.. autoclass:: REPP
   :members:

.. autoclass:: REPPResult(string, startmap, endmap)
   :members:

.. autoclass:: REPPStep(input, output, operation, applied, startmap, endmap)
   :members:


Exceptions
----------

.. autoexception:: REPPError
   :show-inheritance:

.. autoexception:: REPPWarning
   :show-inheritance:
