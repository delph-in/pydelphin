
from collections import Sequence
from datetime import datetime

from delphin.derivation import Derivation
from delphin.tokens import YyTokenLattice
from delphin.mrs import (
    Mrs,
    Dmrs,
    simplemrs,
    eds,
)
from delphin.util import SExpr, stringtypes


class Processor(object):
    """
    Base class for processors.

    This class defines the basic interface for all PyDelphin processors,
    such as :class:`~delphin.interfaces.ace.AceProcess` and
    :class:`~delphin.interfaces.rest.DelphinRestClient`. It can also be
    used to define preprocessor wrappers of other processors such that
    it has the same interface, allowing it to be used, e.g., with
    :meth:`TestSuite.process() <delphin.itsdb.TestSuite.process>`.

    Attributes:
        task: name of the task the processor performs (e.g. `"parse"`,
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

    def tree(self):
        """
        Deserialize and return a labeled syntax tree. The tree data
        may be a standalone datum, or embedded in the derivation.
        """
        tree = self.get('tree')
        if isinstance(tree, stringtypes):
            tree = SExpr.parse(tree).data
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

class ParseResponse(dict):
    """
    A wrapper around the response dictionary for more convenient
    access to results.
    """
    _result_factory = ParseResult

    def __repr__(self):
        return 'ParseResponse({})'.format(dict.__repr__(self))

    def results(self):
        """Return ParseResult objects for each result."""
        return [self._result_factory(r) for r in self.get('results', [])]

    def result(self, i):
        """Return a ParseResult object for the *i*\ th result."""
        return self._result_factory(self.get('results', [])[i])

    def tokens(self, tokenset='internal'):
        """
        Deserialize and return a YyTokenLattice object for the
        initial or internal token set, if provided, from the YY
        format or the JSON-formatted data; otherwise return the
        original string.

        Args:
            tokenset (str): return `'initial'` or `'internal'` tokens
                (default: `'internal'`)
        Returns:
            :class:`YyTokenLattice`
        """
        toks = self.get('tokens', {}).get(tokenset)
        if toks is not None:
            if isinstance(toks, stringtypes):
                toks = YyTokenLattice.from_string(toks)
            elif isinstance(toks, Sequence):
                toks = YyTokenLattice.from_list(toks)
        return toks


class FieldMapper(object):
    """
    A class for mapping respsonses to [incr tsdb()] fields.

    This class provides two methods for mapping responses to fields:

    * map() - takes a response and returns a list of (table, data)
        tuples for the data in the response, as well as aggregating
        any necessary information
    * cleanup() - returns any (table, data) tuples resulting from
        aggregated data over all runs, then clears this data

    Alternative [incr tsdb()] schema can be handled by overriding
    these two methods and the __init__() method.
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
                d['flags'] = SExpr.format(result['flags'])
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
