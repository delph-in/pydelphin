
delphin.interfaces
==================

.. automodule:: delphin.interfaces
 :members:

.. toctree::
   :maxdepth: 2
   :caption: Modules

   delphin.interfaces.ace.rst
   delphin.interfaces.rest.rst

Common Classes
--------------

.. automodule:: delphin.interfaces.base
  :members:


.. _preprocessor-example:

Wrapping a Processor for Preprocessing
--------------------------------------

The :class:`~delphin.interfaces.base.Processor` class can be used to
implement a preprocessor that maintains the same interface as the
underlying processor. The following example wraps an
:class:`~delphin.interfaces.ace.AceParser` instance of the
`English Resource Grammar <http://www.delph-in.net/erg/>`_ with a
:class:`~delphin.repp.REPP` instance.

>>> from delphin.interfaces import ace, base
>>> from delphin import repp
>>> 
>>> class REPPWrapper(base.Processor):
...     def __init__(self, cpu, rpp):
...         self.cpu = cpu
...         self.task = cpu.task
...         self.rpp = rpp
...     def process_item(self, datum, keys=None):
...         preprocessed_datum = str(self.rpp.tokenize(datum))
...         return self.cpu.process_item(preprocessed_datum, keys=keys)
... 
>>> # The preprocessor can be used like a normal Processor:
>>> rpp = repp.REPP.from_config('../../grammars/erg/pet/repp.set')
>>> grm = '../../grammars/erg-1214-x86-64-0.9.27.dat'
>>> with ace.AceParser(grm, cmdargs=['-y']) as _cpu:
...     cpu = REPPWrapper(_cpu, rpp)
...     response = cpu.process_item('Abrams hired Browne.')
...     for result in response.results():
...         print(result.mrs())
... 
<Mrs object (proper named hire proper named) at 140488735960480>
<Mrs object (unknown compound udef named hire parg addressee proper named) at 140488736005424>
<Mrs object (unknown proper compound udef named hire parg named) at 140488736004864>
NOTE: parsed 1 / 1 sentences, avg 1173k, time 0.00986s

A similar technique could be used to manage external processes, such as
`MeCab <http://taku910.github.io/mecab/>`_ for morphological
segmentation of Japanese for `Jacy <http://moin.delph-in.net/JacyTop>`_.
It could also be used to make a postprocessor, a backoff mechanism in
case an input fails to parse, etc.
