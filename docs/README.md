# PyDelphin Documentation

This subdirectory contains the content and configuration files for
PyDelphin's documentation. The official documentation is built by
[Read The Docs](https://readthedocs.org/), but you may want to build
locally to make sure it can build without errors. In order to build
the documentation locally, create a virtual environment called `env`
and install the dependencies. For example:

```bash
pydelphin/docs$ virtualenv -p python3 env
pydelphin/docs$ source env/bin/activate
(env) pydelphin/docs$ pip install sphinx sphinx_rtd_theme
(env) pydelphin/docs$ pip install penman networkx requests Pygments
```

After these steps complete, you should be able to build the
documentation.

## Building the documentation

While in the configured virtual environment, run `make html`:

```bash
(env) pydelphin/docs$ make html
```

## Testing documentation coverage

First run

```bash
(env) pydelphin/docs$ make coverage
```

Then inspect `_build/coverage/python.txt`

