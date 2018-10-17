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
  >>> __version__
  '0.9.0'
  ```
* Python version (e.g. 2.7, 3.4, etc.)

For feature requests, please provide a use case for the feature.

## Submitting code

Please follow these guidelines for code and repository changes:

* [PEP8](https://www.python.org/dev/peps/pep-0008/) style guidelines
* [Git-Flow](http://nvie.com/posts/a-successful-git-branching-model/)
  branching model
* [Semantic Versioning](http://semver.org/)
* PyDelphin is object-oriented in many cases, but avoid unnecessary
  classes when standard Python data structures are sufficient
* In implementing DELPH-IN formalisms and formats, aim first to be
  correct and complete (according to documentation at
  http://moin.delph-in.net/; if a wiki doesn't exist, it's a good idea
  to make one), and secondly convenient. Avoid adding features that
  aren't part of the spec and would have limited utility.
* PyDelphin is a library, not an application, so application code
  belongs in separate repositories. See [gTest][] and [bottlenose][] for
  examples of applications utilizing PyDelphin.
* API documentation is generated from the code and uses docstrings, so
  provide descriptive docstrings for all modules, classs, methods, and
  functions. Follow [Google-style docstrings][] and use
  [reStructuredText][] for formatting.

### Testing

Always run the unit tests before committing.

    tox

[Tox](https://testrun.org/tox/latest/) must be installed, along with
Python versions 2.7, 3.4, 3.5, and 3.6. It creates a virtual environment
in order to run the tests, which helps avoid missing dependencies. For
basic unit testing, you may install [pytest](http://pytest.org/) and
run:

    py.test

But be sure to test against all versions with `tox` prior to committing.

### Test Coverage

Compute test coverage by installing
[pytest-cov](https://github.com/pytest-dev/pytest-cov) and running:

    py.test --cov-report=html --cov=delphin

Note that the codebase doesn't yet have full test coverage.
Contributions of unit tests are very welcome!

## Documentation

The documentation resides in the `docs/` subdirectory, which contains
all content for the tutorials and some content for the API reference.
The bulk of the content for the API reference is in the docstrings of
the modules, classes, and functions of the code itself. Therefore, all
*public* modules, classes, methods, and functions should have
docstrings and should not have a name with a leading underscore, as
otherwise they will not appear in the documentation.

The API reference and tutorials are written in [reStructuredText][]
and generated using [Sphinx][] on the [Read the Docs][] service.
Repository files, such as the README, CHANGELOG, and CONTRIBUTING
fies, are written in [Markdown][].

For instructions on building the documentation, see [docs/](docs).
Do not check in the generated documentation files (e.g., `*.html`);
only documentation source files belong, as the rest will be
generated automatically by [Read the Docs][].


# Release Checklist

Do the following tasks prior to releasing on GitHub and PyPI.

- [ ] Ensure all [issues][] are resolved for the version (check [milestones][])
- [ ] Make the release commit on `develop` branch
  - [ ] Update `CHANGELOG.md`
  - [ ] Update `README.md` (contributors, requirements, etc.) if necessary
  - [ ] Ensure tests pass: `tox`
  - [ ] Ensure the documentation builds without error (see above)
  - [ ] Bump the version in `delphin/__about__.py`
  - [ ] commit
  - [ ] push
- [ ] Merge to master
  - [ ] Test again: `tox`
  - [ ] push
- [ ] Create a source distribution: `setup.py sdist`
- [ ] Build a wheel distribution: `setup.py bdist_wheel --universal`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] [Make a new release](https://github.com/delph-in/pydelphin/releases/new)
- [ ] Announce

[issues]: https://github.com/delph-in/pydelphin/issues
[milestones]: https://github.com/delph-in/pydelphin/milestones
[gTest]: https://github.com/goodmami/gtest
[bottlenose]: https://github.com/delph-in/bottlenose
[CartogrAPI]: https://github.com/goodmami/cartograpi
[RenderDown]: https://github.com/goodmami/renderdown
[Google-style docstrings]: https://google.github.io/styleguide/pyguide.html?showone=Comments#Comments
[Sphinx]: http://www.sphinx-doc.org/
[reStructuredText]: http://docutils.sourceforge.net/
[Read the Docs]: https://readthedocs.org/
[Markdown]: https://github.github.com/gfm/
