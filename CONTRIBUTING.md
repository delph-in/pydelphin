# How to contribute

Basic idea: Fork and submit pull requests!

Please use the [issue tracker][issues], as it creates documentation
for the bugs and features.

Always run the unit tests before committing.

    tox

[Tox](https://testrun.org/tox/latest/) must be installed, along with
Python versions 2.7, 3.3, 3.4, and 3.5. For basic unit testing, you
may instead run:

    ./setup.py test

But be sure to test against all versions with `tox` prior to committing.

If you're contributing an untested bug fix or new code, try to ensure full test
coverage. Coverage can be computed like this:

    ./setup.py coverage

Note that the codebase doesn't yet have full test coverage. Contributions of
unit tests are very welcome!

#### Module Layout

Please follow this general layout (note that the following listing is not
exhaustive):

```bash
delphin/
├── mrs/  # Significant modules related to MRS represenations
│   ├── xmrs.py  # primary pyDelphin structure for MRS representations
│   ├── simplemrs.py  # reading/writing the SimpleMrs format
│   └── (other MRS-specific modules go here)
├── interfaces/  # Code that interacts with external software
│   ├── ace.py
│   └── (other interfaces go here)
├── extra/  # Non-critical code, like syntax highlighters
│   ├── highlight.py
│   └── (other extras go here)
├── lib/  # 3rd party modules (only when necessary!)
│   └── six.py  # for Python 2/3 compatibility
├── derivation.py  # derivation trees
├── itsdb.py  # [incr tsdb()] profiles
├── tdl.py  # TDL code
├── tfs.py  # Basic typed feature structures
└── (other small modules can go here)

```

New packages for DELPH-IN representations (e.g., alongside `mrs/`) can be added,
but they should first exist as simple modules. Then, if there is a need, they
can be promoted to a package (with `__init__.py` scripts to help maintain
import compatibility).

#### Version Compatibility

PyDelphin currently maintains compatibility with Python 2.7 and 3.3+.
Versions prior to 2.6 and 3.0--3.2 are not targeted. Testing with
`tox` will run the unit tests against these versions, so make sure
you have the old versions installed.

#### Branching

See here: http://nvie.com/posts/a-successful-git-branching-model/

Basically, each new changeset (e.g. features or bug fixes) should have
its own branch. Changeset branches (except critical bug fixes) get
merged to the `develop` branch, and `develop` gets merged back to
`master` when a new release is ready.

#### Code Style and Paradigms

Please follow [PEP8](https://www.python.org/dev/peps/pep-0008/) unless there's
a good reason not to. Also try to follow the conventions exemplified in the
existing code.

I try to make pyDelphin more functional than object-oriented, but there's
nothing wrong with adding a new class. If all you need is a container for data,
though, consider a [namedtuple][] or even basic Python data structures (they are
often more efficient). Also try to avoid adding extraneous fields to data
structures, and instead keep them minimal.

[namedtuple]: https://docs.python.org/3/library/collections.html#collections.namedtuple

# Release Checklist

Do the following tasks prior to releasing on GitHub and PyPI.

- [ ] Ensure all [issues][] are resolved for the version (check [milestones][])
- [ ] Make the release commit on `develop` branch
  - [ ] Update `CHANGELOG.md`
  - [ ] Update `README.md` (contributors, requirements, etc.) if necessary
  - [ ] Ensure tests pass: `tox`
  - [ ] Bump the version in `delphin/__about__.py`
  - [ ] commit
  - [ ] push
- [ ] Merge to master
  - [ ] Test again: `tox`
  - [ ] push
- [ ] [Make a new release](https://github.com/delph-in/pydelphin/releases/new)
- [ ] Create a source distribution: `setup.py sdist`
- [ ] Build a wheel distribution: `setup.py bdist_wheel --universal`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Announce

[issues]: https://github.com/delph-in/pydelphin/issues
[milestones]: https://github.com/delph-in/pydelphin/milestones
