
"""
An interface for the ACE processor.

This module provides classes and functions for managing interactive
communication with an open
`ACE <http://sweaglesw.org/linguistics/ace/>`_ process.

Note:
  ACE is required for the functionality in this module, but it is not
  included with PyDelphin. Pre-compiled binaries are available for
  Linux and MacOS: http://sweaglesw.org/linguistics/ace/

  For installation instructions, see:
  http://moin.delph-in.net/AceInstall

The :class:`AceParser`, :class:`AceTransferer`, and
:class:`AceGenerator` classes are used for parsing, transferring, and
generating with ACE. All are subclasses of :class:`AceProcess`, which
connects to ACE in the background, sends it data via its stdin, and
receives responses via its stdout. Responses from ACE are interpreted
so the data is more accessible in Python.

Warning:
  Instantiating :class:`AceParser`, :class:`AceTransferer`, or
  :class:`AceGenerator` opens ACE in a subprocess, so take care to
  close the process (:meth:`AceProcess.close`) when finished or,
  alternatively, instantiate the class in a context manager.

Interpreted responses are stored in a dictionary-like
:class:`~delphin.interfaces.base.ParseResponse` object. When queried
as a dictionary, these objects return the raw response strings. When
queried via its methods, the PyDelphin models of the data are returned.
The response objects may contain a number of
:class:`~delphin.interfaces.ParseResult` objects. These objects
similarly provide raw-string access via dictionary keys and
PyDelphin-model access via methods. Here is an example of parsing a
sentence with :class:`AceParser`:

    >>> with AceParser('erg-1214-x86-64-0.9.24.dat') as parser:
    ...     response = parser.interact('Cats sleep.')
    ...     print(response.result(0)['mrs'])
    ...     print(response.result(0).mrs())
    ... 
    [ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ udef_q<0:4> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] RSTR: h5 BODY: h6 ]  [ _cat_n_1<0:4> LBL: h7 ARG0: x3 ]  [ _sleep_v_1<5:11> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]
    <Xmrs object (udef cat sleep) at 139880862399696>

Functions exist for non-interactive communication with ACE:
:func:`parse` and :func:`parse_from_iterable` open and close an
:class:`AceParser` instance; :func:`transfer` and
:func:`transfer_from_iterable` open and close an :class:`AceTransferer`
instance; and :func:`generate` and :func:`generate_from_iterable` open
and close an :class:`AceGenerator` instance. Note that these functions
open a new ACE subprocess every time they are called, so if you have
many items to process, it is more efficient to use
:func:`parse_from_iterable`, :func:`transfer_from_iterable`, or
:func:`generate_from_iterable` than the single-item versions, or to
interact with the :class:`AceProcess` subclass instances directly.

"""

import logging
import os
import argparse
import re
from subprocess import (
    check_call,
    check_output,
    CalledProcessError,
    Popen,
    PIPE
)
from platform import platform   # portable system information
from getpass import getuser     # portable way to get username
from socket import gethostname  # portable way to get host name
from datetime import datetime
import locale; locale.setlocale(locale.LC_ALL, '')
encoding = locale.getpreferredencoding(False)

from delphin.interfaces.base import ParseResponse, Processor
from delphin.util import SExpr, stringtypes
from delphin.__about__ import __version__ as pydelphin_version


class AceProcess(Processor):
    """
    The base class for interfacing ACE.

    This manages most subprocess communication with ACE, but does not
    interpret the response returned via ACE's stdout. Subclasses
    override the :meth:`receive` method to interpret the task-specific
    response formats.

    Args:
        grm (str): path to a compiled grammar image
        cmdargs (list, optional): a list of command-line arguments
            for ACE; note that arguments and their values should be
            separate entries, e.g. `['-n', '5']`
        executable (str, optional): the path to the ACE binary; if
            `None`, ACE is assumed to be callable via `ace`
        env (dict): environment variables to pass to the ACE
            subprocess
        tsdbinfo (bool): if `True` and ACE's version is compatible,
            all information ACE reports for [incr tsdb()] processing
            is gathered and returned in the response
    """

    #: The name of the task performed by the processor (`'parse'`,
    #: `'transfer'`, or `'generate'`). This is useful when a function,
    #: such as :meth:`delphin.itsdb.TestSuite.process`, accepts any
    #: :class:`AceProcess` instance.
    task = None
    _cmdargs = []
    _termini = []

    def __init__(self, grm, cmdargs=None, executable=None, env=None,
                 tsdbinfo=True, **kwargs):
        if not os.path.isfile(grm):
            raise ValueError("Grammar file %s does not exist." % grm)
        self.grm = grm

        self.cmdargs = cmdargs or []
        # validate the arguments
        _ace_argparser.parse_args(self.cmdargs)

        self.executable = executable or 'ace'
        ace_version = self.ace_version
        if ace_version >= (0, 9, 14):
            self.cmdargs.append('--tsdb-notes')
        if tsdbinfo and ace_version >= (0, 9, 24):
            self.cmdargs.extend(['--tsdb-stdout', '--report-labels'])
            self.receive = self._tsdb_receive
        else:
            self.receive = self._default_receive
        self.env = env or os.environ
        self._run_id = -1
        self.run_infos = []
        self._open()

    @property
    def ace_version(self):
        """The version of the specified ACE binary."""
        return _ace_version(self.executable)

    @property
    def run_info(self):
        """Contextual information about the the running process."""
        return self.run_infos[-1]

    def _open(self):
        self._p = Popen(
            [self.executable, '-g', self.grm] + self._cmdargs + self.cmdargs,
            stdin=PIPE,
            stdout=PIPE,
            env=self.env,
            universal_newlines=True
        )
        self._run_id += 1
        self.run_infos.append({
            'run-id': self._run_id,
            'application': 'ACE {} via PyDelphin v{}'.format(
                '.'.join(map(str, self.ace_version)), pydelphin_version),
            'environment': ' '.join(self.cmdargs),
            'user': getuser(),
            'host': gethostname(),
            'os': platform(),
            'start': datetime.now()
        })

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False  # don't try to handle any exceptions

    def _result_lines(self, termini=None):
        poll = self._p.poll
        next_line = self._p.stdout.readline

        if termini is None:
            termini = self._termini
        i, end = 0, len(termini)
        cur_terminus = termini[i]

        lines = []
        while i < end:
            s = next_line()
            if s == '' and poll() != None:
                logging.info(
                    'Process closed unexpectedly; attempting to reopen'
                )
                self.close()
                self._open()
                break
            # The 'run' note should appear when the process is opened, but
            # handle it here to avoid potential deadlocks if it gets buffered
            elif s.startswith('NOTE: tsdb run:'):
                self._read_run_info(s.rstrip())
            # the rest should be normal result lines
            else:
                lines.append(s.rstrip())
                if cur_terminus.search(s):
                    i += 1
        return [line for line in lines if line != '']

    def _read_run_info(self, line):
        assert line.startswith('NOTE: tsdb run:')
        for key, value in _sexpr_data(line[15:].lstrip()):
            if key == ':application':
                continue  # PyDelphin sets 'application'
            self.run_info[key.lstrip(':')] = value

    def send(self, datum):
        """
        Send *datum* (e.g. a sentence or MRS) to ACE.

        Warning:
          Sending data without reading (e.g., via :meth:`receive`) can
          fill the buffer and cause data to be lost. Use the
          :meth:`interact` method for most data-processing tasks with
          ACE.
        """
        try:
            self._p.stdin.write((datum.rstrip() + '\n'))
            self._p.stdin.flush()
        except (IOError, OSError):  # ValueError if file was closed manually
            logging.info(
                'Attempted to write to a closed process; attempting to reopen'
            )
            self._open()
            self._p.stdin.write((datum.rstrip() + '\n'))
            self._p.stdin.flush()

    def receive(self):
        """
        Return the stdout response from ACE.

        Warning:
            Reading beyond the last line of stdout from ACE can cause
            the process to hang while it waits for the next line. Use
            the :meth:`interact` method for most data-processing tasks
            with ACE.
        """
        raise NotImplementedError()

    def _default_receive(self):
        raise NotImplementedError()

    def _tsdb_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)
        line = ' '.join(lines)  # ACE 0.9.24 on Mac puts superfluous newlines
        response = _tsdb_response(response, line)
        return response

    def interact(self, datum):
        """
        Send *datum* to ACE and return the response.

        This is the recommended method for sending and receiving data
        to/from an ACE process as it reduces the chances of
        over-filling or reading past the end of the buffer. It also
        performs a simple validation of the input to help ensure that
        one complete item is processed at a time.

        If input item identifiers need to be tracked throughout
        processing, see :meth:`process_item`.

        Args:
            datum (str): the input sentence or MRS
        Returns:
            :class:`~delphin.interfaces.ParseResponse`
        """
        validated = self._validate_input(datum)
        if validated:
            self.send(validated)
            result = self.receive()
        else:
            result, lines = _make_response(
                [('NOTE: PyDelphin could not validate the input and '
                  'refused to send it to ACE'),
                 'SKIP: {}'.format(datum)],
                self.run_info)
        result['input'] = datum
        return result

    def process_item(self, datum, keys=None):
        """
        Send *datum* to ACE and return the response with context.

        The *keys* parameter can be used to track item identifiers
        through an ACE interaction. If the `task` member is set on
        the AceProcess instance (or one of its subclasses), it is
        kept in the response as well.
        Args:
            datum (str): the input sentence or MRS
            keys (dict): a mapping of item identifier names and values
        Returns:
            :class:`~delphin.interfaces.ParseResponse`
        """
        response = self.interact(datum)
        if keys is not None:
            response['keys'] = keys
        if 'task' not in response and self.task is not None:
            response['task'] = self.task
        return response

    def close(self):
        """
        Close the ACE process and return the process's exit code.
        """
        self.run_info['end'] = datetime.now()
        self._p.stdin.close()
        for line in self._p.stdout:
            if line.startswith('NOTE: tsdb run:'):
                self._read_run_info(line)
            else:
                logging.debug('ACE cleanup: {}'.format(line.rstrip()))
        retval = self._p.wait()
        return retval


class AceParser(AceProcess):
    """
    A class for managing parse requests with ACE.

    See :class:`AceProcess` for initialization parameters.
    """

    task = 'parse'
    _termini = [re.compile(r'^$'), re.compile(r'^$')]

    def _validate_input(self, datum):
        # valid input for parsing is non-empty
        # (this relies on an empty string evaluating to False)
        return datum.strip()

    def _default_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)
        response['results'] = [
            dict(zip(('mrs', 'derivation'), map(str.strip, line.split(' ; '))))
            for line in lines
        ]
        return response


class AceTransferer(AceProcess):
    """
    A class for managing transfer requests with ACE.

    Note that currently the `tsdbinfo` parameter must be set to `False`
    as ACE is not yet able to provide detailed information for
    transfer results.

    See :class:`AceProcess` for initialization parameters.
    """

    task = 'transfer'
    _termini = [re.compile(r'^$')]

    def __init__(self, grm, cmdargs=None, executable=None, env=None,
                 tsdbinfo=False, **kwargs):
        # disallow --tsdb-stdout
        if tsdbinfo == True:
            raise ValueError(
                'tsdbinfo=True is not available for AceTransferer'
            )
        if '--tsdb-stdout' in (cmdargs or []):
            cmdargs.remove('--tsdb-stdout')
        AceProcess.__init__(
            self, grm, cmdargs=cmdargs, executable=executable, env=env,
            tsdbinfo=False, **kwargs
        )

    def _validate_input(self, datum):
        return _possible_mrs(datum)

    def _default_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)
        response['results'] = [{'mrs': line.strip()} for line in lines]
        return response


class AceGenerator(AceProcess):
    """
    A class for managing realization requests with ACE.

    See :class:`AceProcess` for initialization parameters.
    """

    task = 'generate'
    _cmdargs = ['-e', '--tsdb-notes']
    _termini = [re.compile(r'NOTE: tsdb parse: ')]

    def _validate_input(self, datum):
        return _possible_mrs(datum)

    def _default_receive(self):
        show_tree = '--show-realization-trees' in self.cmdargs
        show_mrs = '--show-realization-mrses' in self.cmdargs

        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)

        i, numlines = 0, len(lines)
        results = []
        while i < numlines:
            result = {'SENT': lines[i].strip()}
            i += 1
            if show_tree and lines[i].startswith('DTREE = '):
                result['derivation'] = lines[i][8:].strip()
                i += 1
            if show_mrs and lines[i].startswith('MRS = '):
                result['mrs'] = lines[i][6:].strip()
                i += 1
            results.append(result)
        response['results'] = results
        return response

    def _tsdb_receive(self):
        # with --tsdb-stdout, the notes line is not printed
        lines = self._result_lines(termini=[re.compile(r'\(:results \.')])
        response, lines = _make_response(lines, self.run_info)
        line = ' '.join(lines)  # ACE 0.9.24 on Mac puts superfluous newlines
        response = _tsdb_response(response, line)
        return response


def compile(cfg_path, out_path, executable=None, env=None, log=None):
    """
    Use ACE to compile a grammar.

    Args:
        cfg_path (str): the path to the ACE config file
        out_path (str): the path where the compiled grammar will be
            written
        executable (str, optional): the path to the ACE binary; if
            `None`, the `ace` command will be used
        env (dict, optional): environment variables to pass to the ACE
            subprocess
        log (file, optional): if given, the file, opened for writing,
            or stream to write ACE's stdout and stderr compile messages
    """
    try:
        check_call(
            [(executable or 'ace'), '-g', cfg_path, '-G', out_path],
            stdout=log, stderr=log, close_fds=True,
            env=(env or os.environ)
        )
    except (CalledProcessError, OSError):
        logging.error(
            'Failed to compile grammar with ACE. See {}'
            .format(log.name if log is not None else '<stderr>')
        )
        raise


def parse_from_iterable(grm, data, **kwargs):
    """
    Parse each sentence in *data* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        data (iterable): the sentences to parse
        **kwargs: additional keyword arguments to pass to the AceParser
    Yields:
        :class:`~delphin.interfaces.ParseResponse`
    Example:
        >>> sentences = ['Dogs bark.', 'It rained']
        >>> responses = list(ace.parse_from_iterable('erg.dat', sentences))
        NOTE: parsed 2 / 2 sentences, avg 723k, time 0.01026s
    """
    with AceParser(grm, **kwargs) as parser:
        for datum in data:
            yield parser.interact(datum)


def parse(grm, datum, **kwargs):
    """
    Parse sentence *datum* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        datum (str): the sentence to parse
        **kwargs: additional keyword arguments to pass to the AceParser
    Returns:
        :class:`~delphin.interfaces.ParseResponse`
    Example:
        >>> response = ace.parse('erg.dat', 'Dogs bark.')
        NOTE: parsed 1 / 1 sentences, avg 797k, time 0.00707s
    """
    return next(parse_from_iterable(grm, [datum], **kwargs))


def transfer_from_iterable(grm, data, **kwargs):
    """
    Transfer from each MRS in *data* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        data (iterable): source MRSs as SimpleMRS strings
        **kwargs: additional keyword arguments to pass to the
            AceTransferer
    Yields:
        :class:`~delphin.interfaces.ParseResponse`
    """
    with AceTransferer(grm, **kwargs) as transferer:
        for datum in data:
            yield transferer.interact(datum)


def transfer(grm, datum, **kwargs):
    """
    Transfer from the MRS *datum* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        datum: source MRS as a SimpleMRS string
        **kwargs: additional keyword arguments to pass to the
            AceTransferer
    Returns:
        :class:`~delphin.interfaces.ParseResponse`
    """
    return next(transfer_from_iterable(grm, [datum], **kwargs))


def generate_from_iterable(grm, data, **kwargs):
    """
    Generate from each MRS in *data* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        data (iterable): MRSs as SimpleMRS strings
        **kwargs: additional keyword arguments to pass to the
            AceGenerator
    Yields:
        :class:`~delphin.interfaces.ParseResponse`
    """
    with AceGenerator(grm, **kwargs) as generator:
        for datum in data:
            yield generator.interact(datum)


def generate(grm, datum, **kwargs):
    """
    Generate from the MRS *datum* with ACE using *grm*.

    Args:
        grm (str): path to a compiled grammar image
        datum: the SimpleMRS string to generate from
        **kwargs: additional keyword arguments to pass to the
            AceGenerator
    Returns:
        :class:`~delphin.interfaces.ParseResponse`
    """
    return next(generate_from_iterable(grm, [datum], **kwargs))


# The following defines the command-line options available for users to
# specify in AceProcess tasks. For a description of these options, see:
#     http://moin.delph-in.net/AceOptions

# thanks: https://stackoverflow.com/a/14728477/1441112
class _ACEArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)

_ace_argparser = _ACEArgumentParser()
_ace_argparser.add_argument('-n', type=int)
_ace_argparser.add_argument('-1', action='store_const', const=1, dest='n')
_ace_argparser.add_argument('-r')
_ace_argparser.add_argument('-p', action='store_true')
_ace_argparser.add_argument('-X', action='store_true')
_ace_argparser.add_argument('-L', action='store_true')
_ace_argparser.add_argument('-y', action='store_true')
_ace_argparser.add_argument('--max-chart-megabytes', type=int)
_ace_argparser.add_argument('--max-unpack-megabytes', type=int)
_ace_argparser.add_argument('--timeout', type=int)
_ace_argparser.add_argument('--disable-subsumption-test', action='store_true')
_ace_argparser.add_argument('--show-realization-trees', action='store_true')
_ace_argparser.add_argument('--show-realization-mrses', action='store_true')
_ace_argparser.add_argument('--show-probability', action='store_true')
_ace_argparser.add_argument('--disable-generalization', action='store_true')
_ace_argparser.add_argument('--ubertagging', nargs='?', type=float)
_ace_argparser.add_argument('--pcfg', type=argparse.FileType())
_ace_argparser.add_argument('--rooted-derivations', action='store_true')
_ace_argparser.add_argument('--udx', nargs='?', choices=('all'))
_ace_argparser.add_argument('--yy-rules', action='store_true')
_ace_argparser.add_argument('--max-words', type=int)


def _ace_version(executable):
    version = (0, 9, 0)  # initial public release
    try:
        out = check_output([executable, '-V'], universal_newlines=True)
        version = re.search(r'ACE version ([.0-9]+)', out).group(1)
        version = tuple(map(int, version.split('.')))
    except (CalledProcessError, OSError):
        logging.error('Failed to get ACE version number.')
        raise
    return version


def _possible_mrs(s):
    start, end = -1, -1
    depth = 0
    for i, c in enumerate(s):
        if c == '[':
            if depth == 0:
                start = i
            depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    # only valid if neither start nor end is -1
    # note: this ignores any secondary MRSs on the same line
    if start != -1 and end != -1:
        # only log if taking a substring
        if start != 0 and end != len(s):
            logging.debug('Possible MRS found at <%d:%d>: %s', start, end, s)
            s = s[start:end]
        return s
    else:
        return False


def _make_response(lines, run):
    response = ParseResponse({
        'NOTES': [],
        'WARNINGS': [],
        'ERRORS': [],
        'run': run,
        'input': None,
        'surface': None,
        'results': []
    })
    content_lines = []
    for line in lines:
        if line.startswith('NOTE: '):
            response['NOTES'].append(line[6:])
        elif line.startswith('WARNING: '):
            response['WARNINGS'].append(line[9:])
        elif line.startswith('ERROR: '):
            response['ERRORS'].append(line[7:])
        elif line.startswith('SENT: ') or line.startswith('SKIP: '):
            response['surface'] = line[6:]
        else:
            content_lines.append(line)
    return response, content_lines


def _sexpr_data(line):
    while line:
        expr = SExpr.parse(line)
        if len(expr.data) != 2:
            logging.error('Malformed output from ACE: {}'.format(line))
            break
        line = expr.remainder.lstrip()
        yield expr.data


def _tsdb_response(response, line):
    for key, val in _sexpr_data(line):
        if key == ':p-input':
            response.setdefault('tokens', {})['initial'] = val.strip()
        elif key == ':p-tokens':
            response.setdefault('tokens', {})['internal'] = val.strip()
        elif key == ':results':
            for result in val:
                res = {}
                for reskey, resval in result:
                    if reskey == ':derivation':
                        res['derivation'] = resval.strip()
                    elif reskey == ':mrs':
                        res['mrs'] = resval.strip()
                    elif reskey == ':surface':
                        res['surface'] = resval.strip()
                    elif isinstance(resval, stringtypes):
                        res[reskey[1:]] = resval.strip()
                    else:
                        res[reskey[1:]] = resval
                response['results'].append(res)
        elif isinstance(val, stringtypes):
            response[key[1:]] = val.strip()
        else:
            response[key[1:]] = val
    return response
