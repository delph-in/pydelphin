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

Questions about PyDelphin can be asked on the [DELPH-IN Discourse
site](https://delphinqa.ling.washington.edu/) in the "PyDelphin Tools"
category.

For bug requests, please provide the following, if possible:

* a minimal working example
* version of PyDelphin (and relevant dependencies)

  ```python
  >>> from delphin.__about__ import __version__
  >>> __version__  # distribution version
  '1.6.0'
  >>> from delphin import mrs
  >>> mrs.__version__  # package version
  '1.6.0'
  ```
* Python version (e.g. 3.7, 3.8, etc.)

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
  https://github.com/delph-in/docs/wiki/; if a wiki doesn't exist,
  it's a good idea to make one), and secondly convenient. Avoid adding
  features that aren't part of the spec and would have limited
  utility.
* PyDelphin is primarily a library, not an application, so application
  code in general belongs in separate repositories. Applications can,
  however, make use of the `delphin` namespace.
* API documentation is generated from the code and uses docstrings, so
  provide descriptive docstrings for all modules, classs, methods, and
  functions. Follow [Google-style docstrings] and use
  [reStructuredText] for formatting.

### Creating a Development Environment

In order to run the tests and build the documentation you'll need to
create a development environment: a virtual environment with the
dependencies installed. First create and activate a virtual
environment from a terminal (the following assumes you have Python 3
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
$ pip install -e .[dev]
```

The `-e` option is an "editable" install, meaning that Python will use
the source files directly (via symlinks) instead of copying them into
the virtual environment. The benefit is that you won't have to
reinstall each time you make a change. The `[dev]` extra installs all
dependencies for testing, building documentation, and uploading
releases. If you just want to run the unit tests, the `[tests]` extra
is sufficient.

### Testing

Always run the unit tests before committing. Simply run pytest from
PyDelphin's top directory to run the unit tests:

```console
$ pytest
```

Note that passing the tests for one version of Python may not be
sufficient for the code to be accepted; it must pass the tests against
all supported versions of Python.

The commands for linting (style and type checking) need some
configuration:

```console
$ flake8 delphin --extend-ignore E221
$ mypy delphin --namespace-packages --explicit-package-bases --ignore-missing-imports
```

These tests will be run automatically when a commit is pushed or pull
request is submitted against the `develop` branch, but it's often more
convenient to run it locally before pushing commits.

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
