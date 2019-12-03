
# PyDelphin Documentation

This subdirectory contains the content and configuration files for
PyDelphin's documentation. The official documentation is built by
[Read The Docs](https://readthedocs.org/), but you may want to build
locally to make sure it can build without errors. In order to build
the documentation locally, install PyDelphin with the `[docs]` or
`[dev]` extras to get the necessary packages. It is recommended that
you use a virtual environment for this.

```console
$ python3 -m venv py3 && source py3/bin/activate  # recommended
$ pip install path/to/pydelphin[docs]
```

For more information, see the documentation about [installing from
source][] and [installing extra dependencies][].  After these steps
complete, you should be able to build the documentation.

[installing from source]: https://pydelphin.readthedocs.io/en/latest/guides/setup.html#installing-from-source
[installing extra dependencies]: https://pydelphin.readthedocs.io/en/latest/guides/setup.html#installing-extra-dependencies

## Building the documentation

After the dependencies have been installed, run `make html`:

```console
$ cd path/to/pydelphin/docs/
$ make html
```

The documentation is then available at `_build/html/index.html`.

## Testing documentation coverage

First run

```console
$ make coverage
```

Then inspect `_build/coverage/python.txt`.
