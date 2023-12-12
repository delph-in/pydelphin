# How to contribute

The easiest way to contribute to PyDelphin is to try it out and enter
bug reports and feature requests. If you're contributing code, fork
the repository and make pull requests to the `main` branch.


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
  '1.9.0'
  >>> from delphin import mrs
  >>> mrs.__version__  # package version
  '1.9.0'
  ```
* Python version (e.g. 3.9, 3.10, etc.)

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

### Testing the code

PyDelphin uses [Hatch](https://hatch.pypa.io/) for managing builds and
dependencies. Install Hatch and use the following commands for testing
your code locally:

```console
$ hatch shell  # activate a virtual environment with PyDelphin installed
$ hatch run dev:lint  # lint the code
$ hatch run dev:typecheck  # type-check the code
$ hatch run dev:test  # run unit tests
$ hatch build  # build a source distribution and wheel
```

Always run the linting, type-checking, and testing commands before
committing. They will be run automatically on pull requests, but its
convenient to make sure everything looks good locally before opening a
pull request.

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

To build the documentation, run the following command:

```console
$ hatch run docs:build
```

Do not check in the generated documentation files (e.g., `*.html`);
only documentation source files belong, as the rest will be
generated automatically by [Read the Docs].
