
"""
DELPH-IN Web API Client
"""

from urllib.parse import urljoin

import requests

from delphin import interface


DEFAULT_SERVER = 'http://erg.delph-in.net/rest/0.9/'


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
            return super().__getitem__(key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return super().get(key, default)


class Client(interface.Processor):
    """
    A class for managing requests to a DELPH-IN Web API server.

    Note:

        This class is not meant to be used directly. Use a subclass
        instead.
    """

    def __init__(self, server):
        self.server = server

    def interact(self, datum, params=None, headers=None):
        """
        Request the server to process *datum* return the response.

        Args:
            datum (str): datum to be processed
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
        params['input'] = datum

        hdrs = {'Accept': 'application/json'}
        if headers is not None:
            hdrs.update(headers)

        url = urljoin(self.server, self.task)
        r = requests.get(url, params=params, headers=hdrs)
        if r.status_code == 200:
            return _HTTPResponse(r.json())
        else:
            r.raise_for_status()

    def process_item(self, datum, keys=None, params=None, headers=None):
        """
        Send *datum* to the server and return the response with context.

        The *keys* parameter can be used to track item identifiers
        through a Web API interaction. If the `task` member is set on
        the Client instance (or one of its subclasses), it is kept in
        the response as well.

        Args:
            datum (str): the input sentence or MRS
            keys (dict): a mapping of item identifier names and values
            params (dict): a dictionary of request parameters
            headers (dict): a dictionary of additional request headers
        Returns:
            :class:`~delphin.interface.Response`
        """
        response = self.interact(datum, params=params, headers=headers)
        if keys is not None:
            response['keys'] = keys
        if 'task' not in response and self.task is not None:
            response['task'] = self.task
        return response


class Parser(Client):
    """
    A class for managing parse requests to a Web API server.
    """

    task = 'parse'


class Generator(Client):
    """
    A class for managing generate requests to a Web API server.
    """

    task = 'generate'


def parse(input, server=DEFAULT_SERVER, params=None, headers=None):
    """
    Request a parse of *input* on *server* and return the response.

    Args:
        input (str): sentence to be parsed
        server (str): the url for the server (LOGON's ERG server is
            used by default)
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
        server=DEFAULT_SERVER,
        params=None,
        headers=None):
    """
    Request parses for all *inputs*.

    Args:
        inputs (iterable): sentences to parse
        server (str): the url for the server (LOGON's ERG server is
            used by default)
        params (dict): a dictionary of request parameters
        headers (dict): a dictionary of additional request headers
    Yields:
        Response objects for each successful response.
    Raises:
        requests.HTTPError: for the first response with a status code
            that is not 200
    """
    client = Parser(server)
    for input in inputs:
        yield client.interact(input, params=params, headers=headers)


def generate(input, server=DEFAULT_SERVER, params=None, headers=None):
    """
    Request realizations for *input*.

    Args:
        input (str): SimpleMRS to be realized
        server (str): the url for the server (LOGON's ERG server is
            used by default)
        params (dict): a dictionary of request parameters
        headers (dict): a dictionary of additional request headers
    Returns:
        A Response containing the results, if the request was
        successful.
    Raises:
        requests.HTTPError: if the status code was not 200
    """
    return next(generate_from_iterable([input], server, params, headers), None)


def generate_from_iterable(
        inputs,
        server=DEFAULT_SERVER,
        params=None,
        headers=None):
    """
    Request realizations for all *inputs*.

    Args:
        inputs (iterable): SimpleMRS strings to realize
        server (str): the url for the server (LOGON's ERG server is
            used by default)
        params (dict): a dictionary of request parameters
        headers (dict): a dictionary of additional request headers
    Yields:
        Response objects for each successful response.
    Raises:
        requests.HTTPError: for the first response with a status code
            that is not 200
    """
    client = Generator(server)
    for input in inputs:
        yield client.interact(input, params=params, headers=headers)
