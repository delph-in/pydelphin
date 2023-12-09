
.. highlight:: console

Requirements, Installation, and Testing
=======================================

PyDelphin releases are available on PyPI_ and the source code is on
GitHub_. For most users, the easiest and recommended way of installing
PyDelphin is from PyPI via :command:`pip`, as it installs any required
dependencies and makes the :command:`delphin` command available (see
:doc:`commands`). If you wish to inspect or contribute code, or if you
need the most up-to-date features, PyDelphin may be used directly from
its source files.

.. _PyPI: https://pypi.org/project/pydelphin/
.. _GitHub: https://github.com/delph-in/pydelphin/


Requirements
------------

PyDelphin works with Python 3.8 and higher, regardless of the
platform. Certain features, however, may require additional
dependencies or may be platform specific, as shown in the table below:

=================================  ============  ===========================
Module or Function                 Dependencies  Notes
=================================  ============  ===========================
:mod:`delphin.ace`                 ACE_          Linux and Mac only
:mod:`delphin.highlight`           Pygments_
:mod:`delphin.web.client`          requests_     ``[web]`` extra
:mod:`delphin.web.server`          Falcon_       ``[web]`` extra
:mod:`delphin.codecs.dmrspenman`   Penman_
:mod:`delphin.codecs.edspenman`    Penman_
:mod:`delphin.repp`                regex_        ``[repp]`` extra
=================================  ============  ===========================

See `Installing Extra Dependencies`_ for information about installing
with "extras", including those needed for PyDelphin development (which
are not listed in the table above).

.. _ACE: http://sweaglesw.org/linguistics/ace/
.. _Pygments: https://pygments.org/
.. _requests: http://python-requests.org/
.. _Falcon: https://falcon.readthedocs.io/
.. _Penman: https://github.com/goodmami/penman
.. _regex: https://bitbucket.org/mrabarnett/mrab-regex/


Installing from PyPI
--------------------

Install the latest releast from PyPI using :command:`pip`::

  [~]$ pip install pydelphin

If you already have an older version of PyDelphin installed, you can
upgrade it by adding the ``--upgrade`` flag to the command.

.. note::

  It is strongly recommended to use virtual environments to keep
  Python packages and dependencies confined to a specific
  environment. For more information, see here:
  https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments


Installing from Source
----------------------

Clone the repository from GitHub to get the latest source code::

  [~]$ git clone https://github.com/delph-in/pydelphin.git

Install from the source code using :command:`pip` as before but give
it the path to the repository instead of the name of the PyPI
project::

  [~]$ cd pydelphin/
  [~/pydelphin]$ pip install .

Installing from source does not require internet access once the
repository has been cloned, but it does require internet to install
any dependencies. Also note that if the project directory is named
``pydelphin`` (the default) and you install from the directory above
it, you mustn't just use the directory name as this will cause
:command:`pip` to install from PyPI_; instead, make it look path-like
by prefixing it with ``./`` (i.e., `pip install ./pydelphin`).

For development, you may also want to use :command:`pip`\ 's `-e`
option to install PyDelphin as "editable", meaning it installs the
dependencies but uses the local source files for PyDelphin's code,
otherwise changes you make to PyDelphin won't be reflected in your
(virtual) environment unless you reinstall PyDelphin.


Installing Extra Dependencies
-----------------------------

Some features require dependencies beyond what the standard install
provides. The purpose of keeping these dependencies optional is to
reduce the install size for users who do not make use of the
additional features.

If you need to use some of these features, such as `delphin.web` and
`delphin.repp`, install the extra dependencies with :command:`pip` as
before but with an install parameter in brackets after
``pydelphin``. For instance::

  [~]$ pip install "pydelphin[web,repp]"

Without the install parameter, the PyDelphin code will still be
installed but its dependencies will not be. The rest of PyDelphin will
work but those features may raise an :exc:`ImportError` or issue a
warning.

The extras that PyDelphin defines are as follows:

===========  ================================================================
Extra        Description
===========  ================================================================
``[web]``    Required for using the :mod:`delphin.web` client and server
``[repp]``   Optional for advanced regex features with :mod:`delphin.repp`
===========  ================================================================


For Contributors
----------------

PyDelphin is built using Hatch_, which also manages dependencies and
commands for testing the code. You will need to `install
<https://hatch.pypa.io/latest/install/>`_ Hatch. Rather than
installing PyDelphin as described above, use the :command:`hatch run`
command to test things, as follows:

  [~/pydelphin]$ hatch run dev:lint  # Linting
  [~/pydelphin]$ hatch run dev:typecheck  # Type-checking
  [~/pydelphin]$ hatch run dev:test  # Unit tests
  [~/pydelphin]$ hatch run docs:build  # Build documentation
  [~/pydelphin]$ hatch build  # build a source distribution and wheel

Hatch will create the ``dev`` and ``docs`` environments as
appropriate, so you do not need to manage virtual environments
yourself for these tasks.

.. _Hatch: https://hatch.pypa.io/
