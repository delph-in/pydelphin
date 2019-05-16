
"""
An interface for the DELPH-IN Web API.

This module provides classes and functions for making requests to
servers that implement the DELPH-IN Web API described here:

    http://moin.delph-in.net/ErgApi

Note:
  Requires `requests` (https://pypi.python.org/pypi/requests)

Basic access is available via the :func:`parse` and
:func:`parse_from_iterable` functions:

>>> from delphin import web
>>> url = 'http://erg.delph-in.net/rest/0.9/'
>>> web.parse('Abrams slept.', server=url)
Response({'input': 'Abrams slept.', 'tcpu': 0.05, ...
>>> web.parse_from_iterable(['Abrams slept.', 'It rained.'], server=url)
<generator object parse_from_iterable at 0x7f546661c258>

If the `server` parameter is not provided to `parse()`, the default
ERG server (as used above) is used by default. Request parameters
(described at http://moin.delph-in.net/ErgApi) can be provided via the
`params` argument.

These functions both instantiate and use the :class:`Client` class,
which manages the connections to a server. It can also be used
directly:

>>> client = web.Client(server=url)
>>> client.parse('Dogs chase cats.')
Response({'input': 'Dogs chase cats.', ...

The server responds with JSON data, which PyDelphin parses to a
dictionary. The responses from :meth:`Client.parse` are then wrapped
in :class:`~delphin.interface.Response` objects, which provide two
methods for inspecting the results. The :meth:`Response.result()
<delphin.interface.Response.result>` method takes a parameter `i` and
returns the *i*\\ th result (0-indexed), and the
:meth:`Response.results() <delphin.interface.Response.results>` method
returns the list of all results. The benefit of using these methods is
that they wrap the result dictionary in a
:class:`~delphin.interface.Result` object, which provides methods for
automatically deserializing derivations, EDS, MRS, or DMRS data. For
example:

>>> r = client.parse('Dogs chase cats', params={'mrs':'json'})
>>> r.result(0)
Result({'result-id': 0, 'score': 0.5938, ...
>>> r.result(0)['mrs']
{'variables': {'h1': {'type': 'h'}, 'x6': ...
>>> r.result(0).mrs()
<Xmrs object (udef dog chase udef cat) at 140000394933248>

If PyDelphin does not support deserialization for a format provided by
the server (e.g. LaTeX output), the original string would be returned
by these methods (i.e. the same as via dict-access).
"""

import requests
from urllib.parse import urljoin

from delphin import interface
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


_default_erg_server = 'http://erg.delph-in.net/rest/0.9/'


class _HTTPResponse(interface.Response):
    """
    This is a interim response object until the server returns a
    'tokens' key.
    """
    def __getitem__(self, key):
        if key == 'tokens' and ('initial' in self or 'internal' in self):
            d = {}
            if 'initial' in self:
                d['initial'] = self['initial']
            if 'internal' in self:
                d['internal'] = self['internal']
            return d
        else:
            return super().__getitem__(self, key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return super().get(key, default)


# For a more harmonious interface (see GitHub issue #141) the
# Client could be subclassed (e.g., DelphinRestParser, etc.)
# and the subclasses fix the parameters and headers at initialization

class Client(interface.Processor):
    """
    A class for managing requests to a DELPH-IN web API server.
    """

    task = 'parse'

    def __init__(self, server=_default_erg_server):
        self.server = server

    def parse(self, sentence, params=None, headers=None):
        """
        Request a parse of *sentence* and return the response.

        Args:
            sentence (str): sentence to be parsed
            params (dict): a dictionary of request parameters
            headers (dict): a dictionary of additional request headers
        Returns:
            A Response containing the results, if the request was
            successful.
        Raises:
            requests.HTTPError: if the status code was not 200
        """
        if params is None:
            params = {}
        params['input'] = sentence

        hdrs = {'Accept': 'application/json'}
        if headers is not None:
            hdrs.update(headers)

        url = urljoin(self.server, 'parse')
        r = requests.get(url, params=params, headers=hdrs)
        if r.status_code == 200:
            return _HTTPResponse(r.json())
        else:
            r.raise_for_status()

    def process_item(self, datum, keys=None, params=None, headers=None):
        response = self.parse(datum, params=params, headers=headers)
        if keys is not None:
            response['keys'] = keys
        if 'task' not in response and self.task is not None:
            response['task'] = self.task
        return response


def parse(input, server=_default_erg_server, params=None, headers=None):
    """
    Request a parse of *input* on *server* and return the response.

    Args:
        input (str): sentence to be parsed
        server (str): the url for the server (the default LOGON server
            is used by default)
        params (dict): a dictionary of request parameters
        headers (dict): a dictionary of additional request headers
    Returns:
        A Response containing the results, if the request was
        successful.
    Raises:
        requests.HTTPError: if the status code was not 200
    """
    return next(parse_from_iterable([input], server, params, headers), None)


def parse_from_iterable(
        inputs,
        server=_default_erg_server,
        params=None,
        headers=None):
    """
    Request parses for all *inputs*.

    Args:
        inputs (iterable): sentences to parse
        server (str): the url for the server (the default LOGON server
            is used by default)
        params (dict): a dictionary of request parameters
        headers (dict): a dictionary of additional request headers
    Yields:
        Response objects for each successful response.
    Raises:
        requests.HTTPError: for the first response with a status code
            that is not 200
    """
    client = Client(server)
    for input in inputs:
        yield client.parse(input, params=params, headers=headers)
