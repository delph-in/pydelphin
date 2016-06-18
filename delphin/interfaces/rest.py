
"""
Client access to the RESTful API for DELPH-IN data.

This module provides classes and functions for making requests to
servers that implement the DELPH-IN web API described here:

    http://moin.delph-in.net/ErgApi

Basic access is available via the parse() and parse_from_iterable()
functions:

    >>> from delphin.interfaces import rest
    >>> url = 'http://erg.delph-in.net/rest/0.9/'
    >>> rest.parse('Abrams slept.', server=url)
    ParseResponse({'input': 'Abrams slept.', 'tcpu': 0.05, ...
    >>> rest.parse_from_iterable(['Abrams slept.', 'It rained.'], server=url)
    <generator object parse_from_iterable at 0x7f546661c258>

If *server* is not provided, the default ERG server (as used above) is
used by default. Request parameters (described at
http://moin.delph-in.net/ErgApi) can be provided via the *params*
argument.

These functions both instantiate and use the DelphinRestClient class,
which manages the connections to a server. It can be used directly:

    >>> client = rest.DelphinRestClient(server=url)
    >>> client.parse('Dogs chase cats.')
    ParseResponse({'input': 'Dogs chase cats.', ...

The server responds with JSON data, which is parsed to a dictionary.
The responses from DelphinRestClient.parse() are then wrapped in
ParseResponse objects, which provide two methods for inspecting the
results. `ParseResponse.result(i)` returns the *i*th result
(0-indexed), and `ParseResponse.results()` returns the list of all
results. The benefit of using these methods is that it wraps the
result dictionary in a ParseResult object, which provides methods for
automatically deserializing derivations, EDS, MRS, or DMRS data. For
example:

    >>> r = client.parse('Dogs chase cats', params={'mrs':'json'})
    >>> r.result(0)
    ParseResult({'result-id': 0, 'score': 0.5938, ...
    >>> r.result(0)['mrs']
    {'variables': {'h1': {'type': 'h'}, 'x6': ...
    >>> r.result(0).mrs()
    <Xmrs object (udef dog chase udef cat) at 140000394933248>

If pyDelphin does not support deserialization for a format provided by
the server (e.g. LaTeX output), the original string would be returned
(i.e. the same as via dict-access).

Requires: requests (https://pypi.python.org/pypi/requests)
"""

import json

import requests
try:
    # Python 3
    from urllib.parse import urljoin
    stringtypes = (str,)
except ImportError:
    from urlparse import urljoin
    stringtypes = (str, unicode)

from delphin.derivation import Derivation
from delphin.mrs import (
    Mrs,
    Dmrs,
    simplemrs,
    eds,
)

default_erg_server = 'http://erg.delph-in.net/rest/0.9/'

class ParseResponse(dict):
    """
    A wrapper around the response dictionary for more convenient
    access to results.
    """

    def __repr__(self):
        return 'ParseResponse({})'.format(dict.__repr__(self))

    def results(self):
        """Return ParseResult objects for each result."""
        return [ParseResult(r) for r in self.get('results', [])]

    def result(self, i):
        """Return a ParseResult object for the *i*th result."""
        return ParseResult(self.get('results', [])[i])

class ParseResult(dict):
    """
    A wrapper around a result dictionary to automate deserialization
    for supported formats. A ParseResult is still a dictionary, so the
    raw data can be obtained using dict access.
    """

    def __repr__(self):
        return 'ParseResult({})'.format(dict.__repr__(self))

    def derivation(self):
        """
        Deserialize and return a Derivation object for UDF- or
        JSON-formatted derivation data; otherwise return the original
        string.
        """
        drv = self.get('derivation')
        if drv is not None:
            if isinstance(drv, dict):
                drv = Derivation.from_dict(drv)
            elif isinstance(drv, stringtypes):
                drv = Derivation.from_string(drv)
        return drv

    def mrs(self):
        """
        Deserialize and return an Mrs object for simplemrs or
        JSON-formatted MRS data; otherwise return the original string.
        """
        mrs = self.get('mrs')
        if mrs is not None:
            if isinstance(mrs, dict):
                mrs = Mrs.from_dict(mrs)
            elif isinstance(mrs, stringtypes):
                mrs = simplemrs.loads_one(mrs)
        return mrs

    def eds(self):
        """
        Deserialize and return an Eds object for native- or
        JSON-formatted EDS data; otherwise return the original string.
        """
        _eds = self.get('eds')
        if _eds is not None:
            if isinstance(_eds, dict):
                _eds = eds.Eds.from_dict(_eds)
            elif isinstance(_eds, stringtypes):
                _eds = eds.loads_one(_eds)
        return _eds

    def dmrs(self):
        """
        Deserialize and return a Dmrs object for JSON-formatted DMRS
        data; otherwise return the original string.
        """
        dmrs = self.get('dmrs')
        if dmrs is not None:
            if isinstance(dmrs, dict):
                dmrs = Dmrs.from_dict(dmrs)
        return dmrs

class DelphinRestClient(object):
    """
    A class for managing requests to a DELPH-IN web API server.
    """
    def __init__(self, server=default_erg_server):
        self.server = server

    def parse(self, sentence, params=None, headers=None):
        """
        Request a parse of *sentence* and return the response.

        Args:
            sentence (str): sentence to be parsed
            params (dict): a dictionary of request parameters
            headers (dict): a dictionary of additional request headers
        Returns:
            A ParseResponse containing the results, if the request was
            successful.
        Raises:
            A requests.HTTPError is raised if the status code was not
            200.
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
            return ParseResponse(r.json())
        else:
            r.raise_for_status()

def parse(input, server=default_erg_server, params=None, headers=None):
    """
    Request a parse of *input* on *server* and return the response.

    Args:
        input (str): sentence to be parsed
        server (str): the url for the server (the default LOGON server
            is used by default)
        params (dict): a dictionary of request parameters
        headers (dict): a dictionary of additional request headers
    Returns:
        A ParseResponse containing the results, if the request was
        successful.
    Raises:
        A requests.HTTPError is raised if the status code was not 200.
    """
    return next(parse_from_iterable([input], server, params, headers), None)

def parse_from_iterable(
        inputs,
        server=default_erg_server,
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
        ParseResponse objects for each successful response.
    Raises:
        A requests.HTTPError is raised for the first response with
        a status code that is not 200.
    """
    client = DelphinRestClient(server)
    for input in inputs:
        yield client.parse(input, params=params, headers=headers)
