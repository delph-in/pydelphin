
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

PyDelphin works with Python versions 2.7 and 3.4+, regardless of the
platform. Certain features, however, may require additional
dependencies or may be platform specific, as shown in the table below:

==============================  ==================  ==================
Module                          Dependencies        Notes
==============================  ==================  ==================
:mod:`delphin.extra.highlight`  Pygments_
:mod:`delphin.extra.latex`      `tikz-dependency`_  LaTeX package
:mod:`delphin.interfaces.ace`   ACE_                Linux and Mac only
:mod:`delphin.interfaces.rest`  requests_
:mod:`delphin.mrs.compare`      NetworkX_
:mod:`delphin.mrs.penman`       Penman_
==============================  ==================  ==================

.. _Pygments: http://pygments.org/
.. _tikz-dependency: https://ctan.org/pkg/tikz-dependency
.. _ACE: http://sweaglesw.org/linguistics/ace/
.. _requests: http://python-requests.org/
.. _NetworkX: https://networkx.github.io/
.. _Penman: https://github.com/goodmami/penman


Installing from PyPI
--------------------

Install the latest releast from PyPI using :command:`pip`::

  $ pip install pydelphin

If you already have PyDelphin installed, you can upgrade it by adding
the ``--upgrade`` flag to the command.

.. note::

  In general, it is a good idea to use virtual environments to keep
  Python packages and dependencies confined to a specific
  environment. For more information, see here:
  https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments


Running from Source
-------------------

Clone the repository from GitHub to get the latest source code::

  $ git clone https://github.com/delph-in/pydelphin.git

By default, cloning the git repository checks out the `develop`
branch. If you want to work in a difference branch (e.g., `master` for
the code of the latest release), you'll need to ``checkout`` the
branch (e.g., ``$ git checkout master``).

In order to use PyDelphin from source, it will need to be importable
by Python. If you are using PyDelphin as a library for your own
project, you can `adjust PYTHONPATH`_ to point to PyDelphin's top
directory, e.g.::

  $ PYTHONPATH=~/path/to/pydelphin/ python myproject.py

.. _adjust PYTHONPATH: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH

Also note that the dependencies of any PyDelphin features you use will
need to be satisfied manually.

Alternatively, :command:`pip` can install PyDelphin from the source
directory instead of from PyPI, and it will detect and install the
dependencies::

  $ pip install ~/path/to/pydelphin/

.. warning::

   The PyDelphin source code can be installed simply by running
   ``$ setup.py install``, but this method is not recommended because
   uninstalling PyDelphin and its dependencies becomes more difficult.


Running Unit Tests
------------------

PyDelphin's unit tests are not distributed on PyPI, so if you wish to
run the unit tests you'll need to get the source code. The tests are
written for pytest_, so one way to run them is
by installing :command:`pytest` (for both Python 2 and 3), and
running::

  $ pytest --doctest-glob=tests/\*.md

A better way to run the tests is using tox_::

  $ tox

The :command:`tox` utility manages the building of virtual
environments for testing, and it uses a configuration file (included
in PyDelphin's sources) that specify how :command:`pytest` should be
called. It can also run the tests for several different Python
versions. Note that simply running :command:`tox` without any options
will attempt to test PyDelphin with every supported version of Python,
and it is likely that some of those versions are not installed on your
system. The ``-e`` option to :command:`tox` can specify the Python
version; e.g., the following runs the tests for Python versions 2.7
and 3.6::

  $ tox -e py27,py36

.. _pytest: http://pytest.org/
.. _tox: https://tox.readthedocs.io/en/latest/
