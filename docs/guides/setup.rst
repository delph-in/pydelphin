
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

PyDelphin works with Python 3.5 and higher, regardless of the
platform. Certain features, however, may require additional
dependencies or may be platform specific, as shown in the table below:

=================================  ============  ===========================
Module or Function                 Dependencies  Notes
=================================  ============  ===========================
:mod:`delphin.ace`                 ACE_          Linux and Mac only
:mod:`delphin.web.client`          requests_     ``[web]`` extra (see below)
:mod:`delphin.web.server`          Falcon_       ``[web]`` extra (see below)
:func:`delphin.mrs.is_isomorphic`  NetworkX_
:mod:`delphin.codecs.dmrspenman`   Penman_
:mod:`delphin.codecs.edspenman`    Penman_
=================================  ============  ===========================

See `Installing Extra Dependencies`_ for information about installing
with "extras", including those needed for PyDelphin development (which
are not listed in the table above).

.. _ACE: http://sweaglesw.org/linguistics/ace/
.. _requests: http://python-requests.org/
.. _Falcon: https://falcon.readthedocs.io/
.. _NetworkX: https://networkx.github.io/
.. _Penman: https://github.com/goodmami/penman


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

By default, cloning the git repository checks out the `develop`
branch. If you want to work in a difference branch (e.g., `master` for
the code of the latest release), you'll need to ``checkout`` the
branch::

  [~]$ cd pydelphin/
  [~/pydelphin]$ git checkout master   # use the latest release
  [~/pydelphin]$ git checkout develop  # use the latest development state

Install from the source code using :command:`pip` as before but give
it the path to the repository instead of the name of the PyPI
project::

  [~/pydelphin]$ pip install .  # when in the repository
  [~]$ pip install ./pydelphin  # when not in the repository

Installing from source does not require internet access once the
repository has been cloned, but it does require internet to install
any dependencies. Also note that if the directory is ``pydelphin``,
just using the directory name will cause :command:`pip` to retrieve it
from PyPI_, so make it look path-like by prefixing it with ``./``.

For development, you may also want to use :command:`pip`\ 's `-e`
option to install PyDelphin as "editable", meaning it installs the
dependencies but uses the local source files for PyDelphin's code,
otherwise changes you make to PyDelphin won't be reflected in your
(virtual) environment unless you reinstall PyDelphin.

.. warning::

   It is not recommended to install from source using ``$ setup.py
   install``, because uninstalling or updating PyDelphin and its
   dependencies becomes more difficult.


Installing Extra Dependencies
-----------------------------

Some features require dependencies beyond what the standard install
provides. The purpose of keeping these dependencies optional is to
reduce the install size for users who do not make use of the
additional features.

If you need to use one of these features, such as `delphin.web`,
install the extra dependencies with :command:`pip` as before but with
an install parameter in brackets after ``pydelphin``. For instance::

  [~]$ pip install pydelphin[web]

Without the install parameter, the code will still be installed but
its dependencies will not be. The rest of PyDelphin will work but
those features may raise an :exc:`ImportError`\.

For developers of PyDelphin there are additional dependencies needed
to run unit tests and build documentation. These are available via the
following install parameters:

- ``test``  -- for unit testing
- ``doc``   -- for building documentation
- ``dev``   -- for making releases (also includes ``test`` and ``doc``)


Running Unit Tests
------------------

PyDelphin's unit tests are not distributed on PyPI, so if you wish to
run the unit tests you'll need to get the source code. The tests are
written for pytest_, which is installed if you used the `test` or
`dev` install parameters described above. Once :command:`pytest` is
installed (note: it may also be called :command:`py.test`), run it to
perform the unit tests::

  [~/pydelphin]$ pytest

This will detect and run any unit tests it finds. It is best to run
the :command:`pytest` in a virtual environment with a clean install of
PyDelphin to ensure that the local Python environment is not
conflicting with PyDelphin's dependencies and also to ensure that
PyDelphin specifies all its dependencies.

If you find it inconvenient to activate several virtual environments
to test the supported Python versions, you may find :command:`tox`
useful. See tox_\ 's website for more information.

.. _pytest: http://pytest.org/
.. _tox: https://tox.readthedocs.io/en/latest/
