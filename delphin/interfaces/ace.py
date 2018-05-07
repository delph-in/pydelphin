
"""
An interface for the ACE processor.

This module provides classes and functions for managing interactive
communication with an open ACE process.

The [AceParser], [AceTransferer], and [AceGenerator] classes are used
for parsing, transferring, and generating with ACE. All are subclasses
of [AceProcess], which connects to ACE in the background, sends it data
via its stdin, and receives responses via its stdout. Responses from ACE
are interpreted so the data is more accessible in Python.

:warning: *Instantiating [AceParser], [AceTransferer], or [AceGenerator]
opens ACE in a subprocess, so take care to [close](#AceProcess-close)
the process when finished (or, alternatively, instantiate the class in a
context manager).*

Interpreted responses are stored in a dictionary-like [ParseResponse]
object. When queried like a dictionary, these objects return the raw
response strings. When queried via its methods, the PyDelphin models of
the data are returned. The response objects may contain a number of
[ParseResult] objects. These objects similarly provide raw-string
access via dictionary keys and PyDelphin-model access via methods. Here
is an example of parsing a sentence with [AceParser]:

    >>> with AceParser('erg-1214-x86-64-0.9.24.dat') as parser:
    ...     response = parser.interact('Cats sleep.')
    ...     print(response.result(0)['mrs'])
    ...     print(response.result(0).mrs())
    ... 
    [ LTOP: h0 INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ] RELS: < [ udef_q<0:4> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] RSTR: h5 BODY: h6 ]  [ _cat_n_1<0:4> LBL: h7 ARG0: x3 ]  [ _sleep_v_1<5:11> LBL: h1 ARG0: e2 ARG1: x3 ] > HCONS: < h0 qeq h1 h5 qeq h7 > ]
    <Xmrs object (udef cat sleep) at 139880862399696>

Functions exist for non-interactive communication with ACE: [parse()]
and [parse_from_iterable()] open and close an AceParser instance;
[transfer()] and [transfer_from_iterable()] open and close an
AceTransferer instance; and [generate()] and [generate_from_iterable()]
open and close an [AceGenerator] instance. Note that these functions
open a new ACE subprocess every time they are called, so if you have
many items to process, it is more efficient to use
[parse_from_iterable()], [transfer_from_iterable()], or
[generate_from_iterable()] than the single-item versions.

Requires: ACE (http://sweaglesw.org/linguistics/ace/)

[AceProcess]: #AceProcess
[AceParser]: #AceParser
[AceTransferer]: #AceTransferer
[AceGenerator]: #AceGenerator
[parse()]: #parse
[parse_from_iterable()]: #parse_from_iterable
[transfer()]: #transfer
[transfer_from_iterable()]: #transfer_from_iterable
[generate()]: #generate
[generate_from_iterable()]: #generate_from_iterable
[ParseResponse]: delphin.interfaces.base#ParseResponse
[ParseResult]: delphin.interfaces.base#ParseResult
"""

import logging
import os
import re
from subprocess import (
    check_call,
    check_output,
    CalledProcessError,
    Popen,
    PIPE
)

import locale; locale.setlocale(locale.LC_ALL, '')
encoding = locale.getpreferredencoding(False)

from delphin.interfaces.base import ParseResponse
from delphin.util import SExpr, stringtypes


class AceProcess(object):
    """
    The base class for interfacing ACE.

    This manages most subprocess communication with ACE, but does not
    interpret the response returned via AceProcess.receive().
    Subclasses override receive() to interpret the task-specific
    response formats.

    Args:
        grm: the path to the compiled grammar file
        cmdargs (list): a list of command-line arguments for ACE;
            note that arguments and their values should be
            separate entries, e.g. ['-n', '5']
        executable: the path to the ACE binary; if `None`, ACE is
            assumed to be callable via `ace`
        env (dict): environment variables to pass to the ACE
            subprocess
        tsdbinfo: if True and ACE is compatible, gather additional
            information from ACE's --tsdb-stdout option
    """

    _cmdargs = []
    _termini = []

    def __init__(self, grm, cmdargs=None, executable=None, env=None,
                 tsdbinfo=True, **kwargs):
        if not os.path.isfile(grm):
            raise ValueError("Grammar file %s does not exist." % grm)
        self.grm = grm
        self.cmdargs = cmdargs or []
        self.executable = executable or 'ace'
        self.env = env or os.environ
        self.ace_version = _ace_version(self.executable)
        if tsdbinfo and self.ace_version >= (0, 9, 24):
            self.cmdargs.extend(['--tsdb-stdout', '--report-labels'])
            self.receive = self._tsdb_receive
        else:
            self.receive = self._default_receive
        self._open()

    def _open(self):
        self._p = Popen(
            [self.executable, '-g', self.grm] + self._cmdargs + self.cmdargs,
            stdin=PIPE,
            stdout=PIPE,
            # stderr=self._stderr,
            env=self.env,
            universal_newlines=True
        )

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
            else:
                lines.append(s.rstrip())
                if cur_terminus.search(s):
                    i += 1
        return [line for line in lines if line != '']

    def send(self, datum):
        """
        Send *datum* (e.g. a sentence or MRS) to ACE.
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
            the process to hang while it waits for the next line.
        """
        raise NotImplementedError()

    def _default_receive(self):
        raise NotImplementedError()

    def _tsdb_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines)
        line = ' '.join(lines)  # ACE 0.9.24 on Mac puts superfluous newlines
        response = _tsdb_response(response, line)
        return response

    def interact(self, datum):
        """
        Send *datum* to ACE and return the response.
        """
        self.send(datum)
        result = self.receive()
        result['input'] = datum
        return result

    def close(self):
        """
        Close the ACE process.
        """
        self._p.stdin.close()
        for line in self._p.stdout:
            logging.debug('ACE cleanup: {}'.format(line.rstrip()))
        retval = self._p.wait()
        return retval


class AceParser(AceProcess):
    """
    A class for managing parse requests with ACE.

    See [AceProcess] for initialization parameters.
    """

    _termini = [re.compile(r'^$'), re.compile(r'^$')]

    def _default_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines)
        response['results'] = [
            dict(zip(('mrs', 'derivation'), map(str.strip, line.split(' ; '))))
            for line in lines
        ]
        return response


class AceTransferer(AceProcess):
    """
    A class for managing transfer requests with ACE.

    See [AceProcess] for initialization parameters.
    """

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

    def _default_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines)
        response['results'] = [{'mrs': line.strip()} for line in lines]
        return response


class AceGenerator(AceProcess):
    """
    A class for managing realization requests with ACE.

    See [AceProcess] for initialization parameters.
    """

    _cmdargs = ['-e', '--tsdb-notes']
    _termini = [re.compile(r'NOTE: tsdb parse: ')]

    def _default_receive(self):
        show_tree = '--show-realization-trees' in self.cmdargs
        show_mrs = '--show-realization-mrses' in self.cmdargs

        lines = self._result_lines()
        response, lines = _make_response(lines)

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
        response, lines = _make_response(lines)
        line = ' '.join(lines)  # ACE 0.9.24 on Mac puts superfluous newlines
        response = _tsdb_response(response, line)
        return response


def compile(cfg_path, out_path, executable=None, env=None, log=None):
    """
    Use ACE to compile a grammar.

    Args:
        cfg_path: the path to the ACE config file
        out_path: the path where the compiled grammar will be written
        executable: the path to the ACE binary; if `None`, ACE is
            assumed to be callable via `ace`
        env (dict): environment variables to pass to the ACE
            subprocess
        log: if given, the path where ACE's stdout and stderr compile
            messages will be written
    """
    #debug('Compiling grammar at {}'.format(abspath(cfg_path)), log)
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
    #debug('Compiled grammar written to {}'.format(abspath(out_path)), log)


def parse_from_iterable(grm, data, **kwargs):
    """
    Parse each sentence in *data* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        data (iterable): the sentences to parse
        kwargs: additional keyword arguments to pass to the AceParser
    """
    with AceParser(grm, **kwargs) as parser:
        for datum in data:
            yield parser.interact(datum)


def parse(grm, datum, **kwargs):
    """
    Parse sentence *datum* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        datum: the sentence to parse
        kwargs: additional keyword arguments to pass to the AceParser
    """
    return next(parse_from_iterable(grm, [datum], **kwargs))


def transfer_from_iterable(grm, data, **kwargs):
    """
    Transfer from each MRS in *data* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        data (iterable): the SimpleMRS strings to transfer from
        kwargs: additional keyword arguments to pass to the
            AceTransferer
    """
    with AceTransferer(grm, **kwargs) as transferer:
        for datum in data:
            yield transferer.interact(datum)


def transfer(grm, datum, **kwargs):
    """
    Transfer from the MRS *datum* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        datum: the SimpleMRS string to transfer from
        kwargs: additional keyword arguments to pass to the
            AceTransferer
    """
    return next(transfer_from_iterable(grm, [datum], **kwargs))


def generate_from_iterable(grm, data, **kwargs):
    """
    Generate from each MRS in *data* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        data (iterable): the SimpleMRS strings to generate from
        kwargs: additional keyword arguments to pass to the
            AceGenerator
    """
    with AceGenerator(grm, **kwargs) as generator:
        for datum in data:
            yield generator.interact(datum)


def generate(grm, datum, **kwargs):
    """
    Generate from the MRS *datum* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        datum: the SimpleMRS string to generate from
        kwargs: additional keyword arguments to pass to the
            AceGenerator
    """
    return next(generate_from_iterable(grm, [datum], **kwargs))


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


def _make_response(lines):
    response = ParseResponse({
        'NOTES': [],
        'WARNINGS': [],
        'ERRORS': [],
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


def _tsdb_response(response, line):
    while line:
        expr = SExpr.parse(line)
        line = expr.remainder
        if len(expr.data) != 2:
            logging.error('Malformed output from ACE: {}'.format(line))
            break
        key, val = expr.data
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
