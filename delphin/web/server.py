
"""
DELPH-IN Web API Server
"""

from typing import Optional, Type
import pathlib
import urllib.parse
import datetime
import json
import functools

import falcon

from delphin import interface
from delphin import ace
from delphin import derivation
from delphin import dmrs
from delphin import eds
from delphin.codecs import (
    simplemrs,
    mrsjson,
    dmrsjson,
    edsjson,
)
from delphin import itsdb
from delphin import tokens


def configure(api, parser=None, generator=None, testsuites=None):
    """
    Configure server application *api*.

    This is the preferred way to setup the server application, but the
    task-specific classes defined in this module can also be used to
    setup custom routes, for instance.

    If a path is given for *parser* or *generator*, it will be used to
    construct a :class:`ParseServer` or :class:`GenerationServer`
    instance, respectively, with default arguments to the underlying
    :class:`~delphin.ace.ACEProcessor`. If non-default arguments are
    needed, pass in the customized :class:`ParseServer` or
    :class:`GenerationServer` instances directly.

    Args:
        api: an instance of :class:`falcon.API`
        parser: a path to a grammar or a :class:`ParseServer` instance
        generator: a path to a grammar or a :class:`GenerationServer`
            instance
        testsuites: mapping of collection names to lists of test suite
            entries
    Example:
        >>> server.configure(
        ...     api,
        ...     parser='~/grammars/erg-2018-x86-64-0.9.30.dat',
        ...     testsuites={
        ...         'gold': [
        ...             {'name': 'mrs',
        ...              'path': '~/grammars/erg/tsdb/gold/mrs'}]})
    """
    if parser is not None:
        if isinstance(parser, (str, pathlib.Path)):
            parser = ParseServer(parser)
        api.add_route('/parse', parser)

    if generator is not None:
        if isinstance(generator, (str, pathlib.Path)):
            generator = GenerationServer(generator)
        api.add_route('/generate', generator)

    if testsuites is not None:
        for collection, entries in testsuites.items():
            collection = '/' + urllib.parse.quote(collection)
            resource = TestSuiteServer(entries)
            api.add_route(collection, resource)
            api.add_route(collection + '/{name}', resource, suffix='name')
            api.add_route(
                collection + '/{name}/{table}', resource, suffix='table')

    api.req_options.strip_url_path_trailing_slash = True
    api.req_options.media_handlers['application/json'] = _json_handler
    api.resp_options.media_handlers['application/json'] = _json_handler


class ProcessorServer(object):
    """
    A server for results from an ACE processor.

    Note:

        This class is not meant to be used directly. Use a subclass
        instead.
    """

    processor_class: Optional[Type[interface.Processor]] = None

    def __init__(self, grammar, *args, **kwargs):
        self.grammar = grammar
        self.args = list(args)
        self.kwargs = kwargs

    def spawn(self, *args):
        cmdargs = self.args + list(args)
        return self.processor_class(
            self.grammar,
            cmdargs,
            **self.kwargs)

    def on_get(self, req, resp):
        inp = req.get_param('input', required=True)
        n = req.get_param_as_int('results', min_value=1, default=1)

        with self.spawn('-n', str(n)) as cpu:
            ace_resp = cpu.interact(inp)

        args = _get_args(req)
        resp.media = _make_response(inp, ace_resp, args)
        resp.status = falcon.HTTP_OK


class ParseServer(ProcessorServer):
    """
    A server for parse results from ACE.
    """

    processor_class = ace.ACEParser


class GenerationServer(ProcessorServer):
    """
    A server for generation results from ACE.
    """

    processor_class = ace.ACEGenerator


def _get_args(req):
    args = {}
    params = req.params
    for name in ('tokens', 'derivation', 'mrs', 'eds', 'dmrs'):
        if name in params:
            val = params[name]
            # handle 'json' and 'null' for ErgAPI compatibility
            args[name] = (val == 'json'
                          or (val != 'null'
                              and req.get_param_as_bool(name)))
        else:
            args[name] = False
    return args


def _make_response(inp, ace_response, params):
    tcpu = ace_response.get('tcpu')
    pedges = ace_response.get('pedges')
    readings = ace_response.get('readings')
    if readings is None:
        readings = len(ace_response.get('results', []))

    results = []
    for i, res in enumerate(ace_response.results()):
        m = res.mrs()
        d = res.derivation()
        result = {'result-id': i}

        if params['derivation']:
            result['derivation'] = d.to_dict(
                fields=['id', 'entity', 'score', 'form', 'tokens'])
        if params['mrs']:
            result['mrs'] = mrsjson.to_dict(m)
        if params['eds']:
            e = eds.from_mrs(m, predicate_modifiers=True)
            result['eds'] = edsjson.to_dict(e)
        if params['dmrs']:
            _d = dmrs.from_mrs(m)
            result['dmrs'] = dmrsjson.to_dict(_d)
        # surface is for generation
        if 'surface' in res:
            result['surface'] = res['surface']

        results.append(result)

    response = {
        'input': inp,
        'readings': readings,
        'results': results
    }
    if tcpu is not None:
        response['tcpu'] = tcpu
    if pedges is not None:
        response['pedges'] = pedges
    if params.get('tokens') == 'json':
        t1 = ace_response.tokens('initial')
        t2 = ace_response.tokens('internal')
        response['tokens'] = {
            'initial': t1.to_list(),
            'internal': t2.to_list()
        }

    return response


class TestSuiteServer(object):
    """
    A server for a collection of test suites.

    Args:
        testsuites: list of test suite descriptions
        transforms: mapping of table names to lists of (column,
            transform) pairs.
    """

    def __init__(self, testsuites, transforms=None):
        self.testsuites = testsuites
        self.index = {entry['name']: entry for entry in testsuites}
        if transforms is None:
            transforms = FIELD_TRANSFORMS
        elif not transforms:
            transforms = []
        self.transforms = dict(transforms)

    def on_get(self, req, resp):
        quote = urllib.parse.quote
        base = req.uri
        data = []
        for entry in self.testsuites:
            name = entry['name']
            uri = '/'.join([base, quote(name)])
            data.append({'name': name, 'url': uri})
        resp.media = data
        resp.status = falcon.HTTP_OK

    def on_get_name(self, req, resp, name):
        try:
            entry = self.index[name]
        except KeyError:
            raise falcon.HTTPNotFound()
        ts = itsdb.TestSuite(entry['path'])
        quote = urllib.parse.quote
        base = req.uri
        resp.media = {tablename: '/'.join([base, quote(tablename)])
                      for tablename in ts.schema}
        resp.status = falcon.HTTP_OK

    def on_get_table(self, req, resp, name, table):
        try:
            entry = self.index[name]
        except KeyError:
            raise falcon.HTTPNotFound()
        ts = itsdb.TestSuite(entry['path'])
        table_ = ts[table]

        limit = req.get_param_as_int('limit', default=len(table_))
        page = req.get_param_as_int('page', default=1)
        rowslice = slice((page - 1) * limit, page * limit)

        rows = []
        transforms = [(table_.column_index(colname), transform)
                      for colname, transform
                      in self.transforms.get(table, [])]
        for row in table_[rowslice]:
            row = list(row)
            for colidx, transform in transforms:
                row[colidx] = transform(row[colidx])
            rows.append(row)

        resp.media = rows
        resp.status = falcon.HTTP_OK


# default field transformers

def _transform_tokens(s):
    return tokens.YYTokenLattice.from_string(s).to_list()


def _transform_mrs(s):
    return mrsjson.to_dict(simplemrs.decode(s))


def _transform_derivation(s):
    return derivation.from_string(s).to_dict()


FIELD_TRANSFORMS = [
    ('parse', [
        ('p-input', _transform_tokens),
        ('p-tokens', _transform_tokens)]),
    ('result', [
        ('mrs', _transform_mrs),
        ('derivation', _transform_derivation)]),
]


# override default JSON handler so it can serialize datetime

def _datetime_default(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    else:
        raise TypeError(type(obj))


_json_handler = falcon.media.JSONHandler(
    dumps=functools.partial(json.dumps, default=_datetime_default),
    loads=json.loads
)
