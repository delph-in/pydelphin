# How to contribute

The easiest way to contribute to PyDelphin is to try it out and enter
bug reports and feature requests. If you're contributing code, fork
the repository and make pull requests to the `develop` branch.

## Filing issues

File issues here: https://github.com/delph-in/pydelphin/issues

Please use the issue tracker for:

* bug reports
* feature requests
* documentation requests
* PyDelphin questions

For bug requests, please provide the following, if possible:

* a minimal working example
* version of PyDelphin (and relevant dependencies)

  ```python
  >>> from delphin.__about__ import __version__
  >>> __version__  # distribution version
  '1.5.0'
  >>> from delphin import mrs
  >>> mrs.__version__  # package version
  '1.5.0'
  ```
* Python version (e.g. 3.6, 3.7, etc.)

For feature requests, please provide a use case for the feature.

## Submitting code

Please follow these guidelines for code and repository changes:

* [PEP8](https://www.python.org/dev/peps/pep-0008/) style guidelines
* [GitHub Flow](https://guides.github.com/introduction/flow/)
  branching model
* [Semantic Versioning](http://semver.org/)
* PyDelphin is object-oriented in many cases, but avoid unnecessary
  classes when standard Python data structures are sufficient
* In implementing DELPH-IN formalisms and formats, aim first to be
  correct and complete (according to documentation at
  http://moin.delph-in.net/; if a wiki doesn't exist, it's a good idea
  to make one), and secondly convenient. Avoid adding features that
  aren't part of the spec and would have limited utility.
* PyDelphin is primarily a library, not an application, so application
  code in general belongs in separate repositories. Applications can,
  however, make use of the `delphin` namespace.
* API documentation is generated from the code and uses docstrings, so
  provide descriptive docstrings for all modules, classs, methods, and
  functions. Follow [Google-style docstrings] and use
  [reStructuredText] for formatting.

### Testing

Always run the unit tests before committing. First, from a terminal
with PyDelphin's top-level directory as the current working directory,
create a virtual environment (the following assumes you have Python 3
installed; the commands may differ depending on your operating system
and choice of shell):

* Linux/macOS

  ```console
  $ python3 -m venv env
  $ source env/bin/activate
  ```

* Windows

  ```console
  > py -3 -m venv env
  > .\env\Scripts\Activate.ps1
  ```

Once activated, you should see `(env)` in the shell prompt. You can
then install PyDelphin's dependencies and run tests with the current
version of Python:

```console
$ pip install .[test]
$ pytest
...
```

To run the tests for all supported versions of Python, a tool like
[Tox](https://tox.readthedocs.io/) is helpful. First install `tox`:

```console
$ pip install tox
```

Then create a `tox.ini` file in the same directory as `setup.py`:

    [tox]
    envlist = py36,py37,py38,py39

    [testenv]
    usedevelop = True
    extras = tests
    commands = pytest

Then you can run `tox` which will create virtual environments and run
`pytest` for each version (note: you need to have each of those
versions of Python installed for it to work):

```console
$ tox
```

### Test Coverage

Compute test coverage by installing
[pytest-cov](https://github.com/pytest-dev/pytest-cov) and running:

    pytest --cov-report=html --cov=delphin

Note that the codebase doesn't yet have full test coverage.
Contributions of unit tests are very welcome!

## Documentation

The documentation resides in the `docs/` subdirectory, which contains
all content for the guides and some structural content for the API
reference. The bulk of the content for the API reference is in the
docstrings of the modules, classes, and functions of the code
itself. Therefore, all *public* modules, classes, methods, and
functions should have docstrings and should not have a name with a
leading underscore, as otherwise they will not appear in the
documentation.

The API reference and tutorials are written in [reStructuredText]
and generated using [Sphinx] on the [Read the Docs] service.
Repository files, such as the README, CHANGELOG, and CONTRIBUTING
files, are written in [Markdown].

For instructions on building the documentation, see [docs/](docs).
Do not check in the generated documentation files (e.g., `*.html`);
only documentation source files belong, as the rest will be
generated automatically by [Read the Docs].


# Release Checklist

Do the following tasks prior to releasing on GitHub and PyPI.

- [ ] Create a branch for the release (e.g., `vX.Y.Z`)
- [ ] Merge into the release branch all features and fixes slated for the release
- [ ] Create a pull request for the version
  - [ ] Ensure all related [issues] are resolved (check [milestones])
  - [ ] Ensure tests pass
  - [ ] Ensure the documentation builds without error (see above)
  - [ ] Bump the version in `delphin/__about__.py`
  - [ ] Update `README.md` if necessary
  - [ ] Update `CHANGELOG.md` (header for version with release date)
  - [ ] Merge
- [ ] [Make a new release](https://github.com/delph-in/pydelphin/releases/new)
- [ ] Ensure PyPI release was uploaded automatically (see [actions])
- [ ] Announce

[issues]: https://github.com/delph-in/pydelphin/issues
[milestones]: https://github.com/delph-in/pydelphin/milestones
[actions]: https://github.com/delph-in/pydelphin/actions
[Google-style docstrings]: https://google.github.io/styleguide/pyguide.html?showone=Comments#Comments
[Sphinx]: http://www.sphinx-doc.org/
[reStructuredText]: http://docutils.sourceforge.net/
[Read the Docs]: https://readthedocs.org/
[Markdown]: https://github.github.com/gfm/
