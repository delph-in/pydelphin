# How to contribute

Basic idea: Fork and submit pull requests!

Please use the issue tracker
(https://github.com/goodmami/pydelphin/issues), as it creates
documentation for the bugs and features.

Always run the unit tests before committing.

    ./setup.py test

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

I aim for pyDelphin to be compatible with both Python 2 and 3, but
it's not a strict requirement. pyDelphin is firstly a Python 3
library, so patches should guarantee Python 3 compatibility first,
and then Python 2 if possible.

More specifically, pyDelphin should first be compatible with Python
3.3+, and then 2.7. After that, as far as is possible without
significant effort or awkward contortions, compatibility for 3.1 and
3.2 can be added. Support for 2.6 or earlier is not a goal.

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
