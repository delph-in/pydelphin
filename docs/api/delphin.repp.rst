
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
