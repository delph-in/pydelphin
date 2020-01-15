
delphin.cli
===========

Command-line Interface Modules

The `delphin.cli` package is a `namespace package
<https://www.python.org/dev/peps/pep-0420>`_ for modules that define
command-line interfaces. Each module under `delphin.cli` must have a
dictionary named ``COMMAND_INFO`` and defined as follows:

.. code-block:: python

   COMMAND_INFO = {
       'name': 'command-name',             # Required
       'help': 'short help message',       # Optional
       'description': 'long description',  # Optional
       'parser': parser,                   # Required
   }

The ``name`` field is the subcommand (e.g., :command:`delphin
command-name`) and the ``parser`` field is a
:py:class:`argparse.ArgumentParser` instance that specifies available
arguments. Some common options, such as ``--verbose`` (``-v``),
``--quiet`` (``-q``), and ``--version`` (``-V``) will be created
automatically by PyDelphin. This parser should also specify a ``func``
callable attribute that is called when the subcommand is used. Thus,
the recommended way to create ``parser`` is as follows:

.. code-block:: python

   parser = argparse.ArgumentParser(add_help=False)
   parser.set_defaults(func=my_function)

All of the default commands in :mod:`delphin.commands` define their
command-line interface in the ``delphin.cli`` namespace.
