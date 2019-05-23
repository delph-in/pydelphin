# -*- coding: utf-8 -*-

"""
Interfaces for external data providers.

This module manages the communication between data providers, namely
processors like `ACE <http://sweaglesw.org/linguistics/ace/>`_ or
remote services like the `DELPH-IN Web API
<http://moin.delph-in.net/ErgApi>`_, and user code or storage
backends, namely [incr tsdb()] :doc:`test suites <delphin.itsdb>`. An
interface sends requests to a provider, then receives and interprets
the response.

The interface may also detect and deserialize supported DELPH-IN
formats if the appropriate modules are available.
"""

from collections import Sequence
from datetime import datetime

from delphin import util
from delphin import exceptions
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


class InterfaceError(exceptions.PyDelphinException):
    """Raised on invalid interface operations."""


class Processor(object):
    """
    Base class for processors.

    This class defines the basic interface for all PyDelphin processors,
    such as :class:`~delphin.ace.ACEProcess` and
    :class:`~delphin.web.Client`. It can also be
    used to define preprocessor wrappers of other processors such that
    it has the same interface, allowing it to be used, e.g., with
    :meth:`TestSuite.process() <delphin.itsdb.TestSuite.process>`.

    Attributes:
        task: name of the task the processor performs (e.g., `"parse"`,
            `"transfer"`, or `"generate"`)
    """

    task = None

    def process_item(self, datum, keys=None):
        """
        Send *datum* to the processor and return the result.

        This method is a generic wrapper around a processor-specific
        processing method that keeps track of additional item and
        processor information. Specifically, if *keys* is provided,
        it is copied into the `keys` key of the response object, and
        if the processor object's `task` member is non-`None`, it is
        copied into the `task` key of the response. These help with
        keeping track of items when many are processed at once, and
        to help downstream functions identify what the process did.

        Args:
            datum: the item content to process
            keys: a mapping of item identifiers which will be copied
                into the response
        """
        raise NotImplementedError()


class Result(dict):
    """
    A wrapper around a result dictionary to automate deserialization
    for supported formats. A Result is still a dictionary, so the
    raw data can be obtained using dict access.
    """

    def __repr__(self):
        return 'Result({})'.format(dict.__repr__(self))

    def derivation(self):
        """
        Interpret and return a Derivation object.

        If :mod:`delphin.derivation` is available and the value of the
        `derivation` key in the result dictionary is a valid UDF
        string or a dictionary, return the interpeted
        Derivation object. If there is no 'derivation' key in the
        result, return `None`.

        Raises:
            InterfaceError: when the value is an unsupported type or
                :mod:`delphin.derivation` is unavailable
        """
        drv = self.get('derivation')
        try:
            from delphin import derivation
            if isinstance(drv, dict):
                drv = derivation.from_dict(drv)
            elif isinstance(drv, str):
                drv = derivation.from_string(drv)
            elif drv is not None:
                raise TypeError(drv.__class__.__name__)
        except (ImportError, TypeError) as exc:
            raise InterfaceError('can not get Derivation object') from exc
        return drv

    def tree(self):
        """
        Interpret and return a labeled syntax tree.

        The tree data may be a standalone datum, or embedded in a
        derivation.
        """
        tree = self.get('tree')

        if isinstance(tree, str):
            tree = util.SExpr.parse(tree).data

        elif tree is None:
            drv = self.get('derivation')
            if isinstance(drv, dict) and 'label' in drv:

                def _extract_tree(d):
                    t = [d.get('label', '')]
                    if 'tokens' in d:
                        t.append([d.get('form', '')])
                    else:
                        for dtr in d.get('daughters', []):
                            t.append(_extract_tree(dtr))
                    return t

                tree = _extract_tree(drv)

        return tree

    def mrs(self):
        """
        Interpret and return an MRS object.

        If :mod:`delphin.codecs.simplemrs` is available and the value
        of the `mrs` key in the result is a valid SimpleMRS string, or
        if :mod:`delphin.codecs.mrsjson` is available and the value is
        a dictionary, return the interpreted MRS object. If there is
        no `mrs` key in the result, return `None`.

        Raises:
            InterfaceError: when the value is an unsupported type or
                the corresponding module is unavailable
        """
        mrs = self.get('mrs')
        try:
            if isinstance(mrs, dict):
                from delphin.codecs import mrsjson
                mrs = mrsjson.from_dict(mrs)
            elif isinstance(mrs, str):
                from delphin.codecs import simplemrs
                mrs = simplemrs.decode(mrs)
            elif mrs is not None:
                raise TypeError(mrs.__class__.__name__)
        except (ImportError, TypeError) as exc:
            raise InterfaceError('can not get MRS object') from exc
        return mrs

    def eds(self):
        """
        Interpret and return an Eds object.

        If :mod:`delphin.codecs.eds` is available and the value of the
        `eds` key in the result is a valid "native" EDS serialization,
        or if :mod:`delphin.codecs.edsjson` is available and the value
        is a dictionary, return the interpreted EDS object. If there
        is no `eds` key in the result, return `None`.

        Raises:
            InterfaceError: when the value is an unsupported type or
                the corresponding module is unavailable
        """
        eds = self.get('eds')
        try:
            if isinstance(eds, dict):
                from delphin.codecs import edsjson
                eds = edsjson.from_dict(eds)
            elif isinstance(eds, str):
                from delphin.codecs import eds as edsnative
                eds = edsnative.decode(eds)
            elif eds is not None:
                raise TypeError(eds.__class__.__name__)
        except (ImportError, TypeError) as exc:
            raise InterfaceError('can not get EDS object') from exc
        return eds

    def dmrs(self):
        """
        Interpret and return a Dmrs object.

        If :mod:`delphin.codecs.dmrsjson` is available and the value
        of the `dmrs` key in the result is a dictionary, return the
        interpreted DMRS object. If there is no `dmrs` key in the
        result, return `None`.

        Raises:
            InterfaceError: when the value is not a dictionary or
                :mod:`delphin.codecs.dmrsjson` is unavailable
        """
        dmrs = self.get('dmrs')
        try:
            if isinstance(dmrs, dict):
                from delphin.codecs import dmrsjson
                dmrs = dmrsjson.from_dict(dmrs)
            elif dmrs is not None:
                raise TypeError(dmrs.__class__.__name__)
        except (ImportError, TypeError) as exc:
            raise InterfaceError('can not get DMRS object') from exc
        return dmrs


class Response(dict):
    """
    A wrapper around the response dictionary for more convenient
    access to results.
    """
    _result_cls = Result

    def __repr__(self):
        return 'Response({})'.format(dict.__repr__(self))

    def results(self):
        """Return Result objects for each result."""
        return [self._result_cls(r) for r in self.get('results', [])]

    def result(self, i):
        """Return a Result object for the result *i*."""
        return self._result_cls(self.get('results', [])[i])

    def tokens(self, tokenset='internal'):
        """
        Interpret and return a YYTokenLattice object.

        If *tokenset* is a key under the `tokens` key of the response,
        interpret its value as a :class:`YYTokenLattice` from a valid
        YY serialization or from a dictionary. If *tokenset* is not
        available, return `None`.

        Args:
            tokenset (str): return `'initial'` or `'internal'` tokens
                (default: `'internal'`)
        Returns:
            :class:`YYTokenLattice`
        Raises:
            InterfaceError: when the value is an unsupported type or
                :mod:`delphin.tokens` is unavailble
        """
        toks = self.get('tokens', {}).get(tokenset)
        try:
            from delphin import tokens
            if isinstance(toks, str):
                toks = tokens.YYTokenLattice.from_string(toks)
            elif isinstance(toks, Sequence):
                toks = tokens.YYTokenLattice.from_list(toks)
            elif toks is not None:
                raise TypeError(toks.__class__.__name__)
        except (KeyError, ImportError, TypeError) as exc:
            raise InterfaceError('can not get YYTokenLattice object') from exc
        return toks


class FieldMapper(object):
    """
    A class for mapping responses to [incr tsdb()] fields.

    This class provides two methods for mapping responses to fields:

    * map() - takes a response and returns a list of (table, data)
        tuples for the data in the response, as well as aggregating
        any necessary information
    * cleanup() - returns any (table, data) tuples resulting from
        aggregated data over all runs, then clears this data

    In addition, the :attr:`affected_tables` attribute should list
    the names of tables that become invalidated by using this
    FieldMapper to process a profile. Generally this is the list of
    tables that :meth:`map` and :meth:`cleanup` create records for,
    but it may also include those that rely on the previous set
    (e.g., treebanking preferences, etc.).

    Alternative [incr tsdb()] schema can be handled by overriding
    these two methods and the __init__() method.

    Attributes:
        affected_tables: list of tables that are affected by the
            processing
    """
    def __init__(self):
        # the parse keys exclude some that are handled specially
        self._parse_keys = '''
            ninputs ntokens readings first total tcpu tgc treal words
            l-stasks p-ctasks p-ftasks p-etasks p-stasks
            aedges pedges raedges rpedges tedges eedges ledges sedges redges
            unifications copies conses symbols others gcs i-load a-load
            date error comment
        '''.split()
        self._result_keys = '''
            result-id time r-ctasks r-ftasks r-etasks r-stasks size
            r-aedges r-pedges derivation surface tree mrs
        '''.split()
        self._run_keys = '''
            run-comment platform protocol tsdb application environment
            grammar avms sorts templates lexicon lrules rules
            user host os start end items status
        '''.split()
        self._parse_id = -1
        self._runs = {}
        self._last_run_id = -1

        self.affected_tables = '''
            run parse result rule output edge tree decision preference
            update fold score
        '''.split()

    def map(self, response):
        """
        Process *response* and return a list of (table, rowdata) tuples.
        """
        inserts = []

        parse = {}
        # custom remapping, cleanup, and filling in holes
        parse['i-id'] = response.get('keys', {}).get('i-id', -1)
        self._parse_id = max(self._parse_id + 1, parse['i-id'])
        parse['parse-id'] = self._parse_id
        parse['run-id'] = response.get('run', {}).get('run-id', -1)
        if 'tokens' in response:
            parse['p-input'] = response['tokens'].get('initial')
            parse['p-tokens'] = response['tokens'].get('internal')
            if 'ninputs' not in response:
                toks = response.tokens('initial')
                if toks is not None:
                    response['ninputs'] = len(toks.tokens)
            if 'ntokens' not in response:
                toks = response.tokens('internal')
                if toks is not None:
                    response['ntokens'] = len(toks.tokens)
        if 'readings' not in response and 'results' in response:
            response['readings'] = len(response['results'])
        # basic mapping
        for key in self._parse_keys:
            if key in response:
                parse[key] = response[key]
        inserts.append(('parse', parse))

        for result in response.get('results', []):
            d = {'parse-id': self._parse_id}
            if 'flags' in result:
                d['flags'] = util.SExpr.format(result['flags'])
            for key in self._result_keys:
                if key in result:
                    d[key] = result[key]
            inserts.append(('result', d))

        if 'run' in response:
            run_id = response['run'].get('run-id', -1)
            # check if last run was not closed properly
            if run_id not in self._runs and self._last_run_id in self._runs:
                last_run = self._runs[self._last_run_id]
                if 'end' not in last_run:
                    last_run['end'] = datetime.now()
            self._runs[run_id] = response['run']
            self._last_run_id = run_id

        return inserts

    def cleanup(self):
        """
        Return aggregated (table, rowdata) tuples and clear the state.
        """
        inserts = []

        last_run = self._runs[self._last_run_id]
        if 'end' not in last_run:
            last_run['end'] = datetime.now()

        for run_id in sorted(self._runs):
            run = self._runs[run_id]
            d = {'run-id': run.get('run-id', -1)}
            for key in self._run_keys:
                if key in run:
                    d[key] = run[key]
            inserts.append(('run', d))

        # reset for next task
        self._parse_id = -1
        self._runs = {}
        self._last_run_id = -1

        return inserts
