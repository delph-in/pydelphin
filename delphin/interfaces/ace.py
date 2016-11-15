
"""
An interface for the ACE parser/generator.

Classes exist for managing interactive communication with an open ACE
process, such as AceParser for parsing sentences, and AceGenerator for
realizing sentences from Xmrs objects. In addition, there are
functions that can be used for one-off jobs, where the ACE process is
killed after the data are processed. The parse() and
parse_from_iterable() functions open and close an AceParser instance,
while generate() and generate_from_iterable() open and close an
AceGenerator instance.

Requires: ACE (http://sweaglesw.org/linguistics/ace/)
"""

import logging
import os
import re
from subprocess import (
    check_call,
    check_output,
    CalledProcessError,
    Popen,
    PIPE,
    STDOUT
)

import locale; locale.setlocale(locale.LC_ALL, '')
encoding = locale.getpreferredencoding(False)

import warnings
warnings.warn(
    'Responses from the ACE interface will use a response class '
    '(like delphin.interfaces.rest) in future releases and may not '
    'be entirely compatible with the current format.',
    FutureWarning
)

from delphin.interfaces.base import ParseResponse, ParseResult
from delphin.util import SExpr, stringtypes

class _AceResult(ParseResult):
    """
    This is a interim response object until the old behavior can be
    removed (maybe v0.6.0).
    """
    def __getitem__(self, key):
        key = {
            'mrs': 'MRS',
            'derivation': 'DERIV',
            'surface': 'SENT',
        }.get(key, key)
        return ParseResult.__getitem__(self, key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return ParseResult.get(self, key, default)


class _AceResponse(ParseResponse):
    """
    This is a interim response object until the old behavior can be
    removed (maybe v0.6.0).
    """
    _result_factory = _AceResult
    def __getitem__(self, key):
        key = {
            'input': 'INPUT',
            'results': 'RESULTS',
        }.get(key, key)
        return ParseResponse.__getitem__(self, key)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return ParseResponse.get(key, default)


class AceProcess(object):
    """
    The base class for interfacing ACE.

    This manages most subprocess communication with ACE, but does not
    interpret the response returned via AceProcess.receive().
    Subclasses override receive() to interpret the task-specific
    response formats.
    """

    _cmdargs = []

    def __init__(self, grm, cmdargs=None, executable=None, env=None,
                 tsdbinfo=True, **kwargs):
        """
        Args:
            grm: the path to the compiled grammar file
            cmdargs (list): a list of command-line arguments for ACE;
                note that arguments and their values should be
                separate entries, e.g. ['-n', '5']
            executable: the path to the ACE binary; if `None`, ACE is
                assumed to be callable via `ace`
            env (dict): environment variables to pass to the ACE
                subprocess
        """
        if not os.path.isfile(grm):
            raise ValueError("Grammar file %s does not exist." % grm)
        self.grm = grm
        self.cmdargs = cmdargs or []
        self.executable = executable or 'ace'
        self.env = env or os.environ
        self.ace_version = _ace_version(self.executable)
        if tsdbinfo and self.ace_version >= (0, 9, 24):
            self.cmdargs.extend(['--tsdb-stdout', '--report-labels'])
        self._open()

    def _open(self):
        self._p = Popen(
            [self.executable, '-g', self.grm] + self._cmdargs + self.cmdargs,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            env=self.env,
            universal_newlines=False  # See _readlines() docstring
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False  # don't try to handle any exceptions

    def send(self, datum):
        """
        Send *datum* (e.g. a sentence or MRS) to ACE.
        """
        self._p.stdin.write((datum.rstrip() + '\n').encode('utf-8'))
        self._p.stdin.flush()

    def receive(self):
        """
        Return the stdout response from ACE.

        Warning:
            Reading beyond the last line of stdout from ACE can cause
            the process to hang while it waits for the next line.
        """
        return self._p.stdout

    def interact(self, datum):
        """
        Send *datum* to ACE and return the response.
        """
        self.send(datum)
        result = self.receive()
        result['INPUT'] = datum
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
    """

    def receive(self):
        if '--tsdb-stdout' in self.cmdargs:
            receive =  _tsdb_stdout_parse
        else:
            receive = _stdout_parse
        return receive(_readlines(self._p.stdout))


class AceGenerator(AceProcess):
    """
    A class for managing realization requests with ACE.
    """

    _cmdargs = ['-e']

    def receive(self):
        if '--tsdb-stdout' in self.cmdargs:
            receive =  _tsdb_stdout_realization
        else:
            receive = _stdout_realization
        return receive(_readlines(self._p.stdout))


def compile(cfg_path, out_path, log=None):
    """
    Use ACE to compile a grammar.

    Args:
        cfg_path: the path to the ACE config file
        out_path: the path where the compiled grammar will be written
        log: if given, the path where ACE's stdout and stderr compile
            messages will be written
    """
    #debug('Compiling grammar at {}'.format(abspath(cfg_path)), log)
    try:
        check_call(
            ['ace', '-g', cfg_path, '-G', out_path],
            stdout=log, stderr=log, close_fds=True
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
    Parse *datum* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        datum: the sentence to parse
        kwargs: additional keyword arguments to pass to the AceParser
    """
    return next(parse_from_iterable(grm, [datum], **kwargs))


def generate_from_iterable(grm, data, **kwargs):
    """
    Generate from each Xmrs in *data* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        data (iterable): the Xmrs objects to generate from
        kwargs: additional keyword arguments to pass to the
            AceGenerator
    """
    with AceGenerator(grm, **kwargs) as generator:
        for datum in data:
            yield generator.interact(datum)


def generate(grm, datum, **kwargs):
    """
    Generate from the Xmrs *datum* with ACE using *grm*.

    Args:
        grm: the path to the grammar image
        datum: the Xmrs object to generate from
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

def _stdout_parse(line_iter):
    response = _AceResponse({
        'INPUT': None,
        'NOTES': [],
        'WARNINGS': [],
        'ERRORS': [],
        'SENT': None,
        'RESULTS': []
    })

    blank = 0

    line = next(line_iter)
    while True:
        if line.strip() == '':
            blank += 1
            if blank >= 2:
                break
        elif line.startswith('SENT: ') or line.startswith('SKIP: '):
            response['SENT'] = line.split(': ', 1)[1]
        elif (line.startswith('NOTE: ') or
              line.startswith('WARNING: ') or
              line.startswith('ERROR: ')):
            level, message = line.split(': ', 1)
            response['%sS' % level].append(message)
        else:
            mrs, deriv = line.split(' ; ')
            response['RESULTS'].append({
                'MRS': mrs.strip(),
                'DERIV': deriv.strip()
            })
        line = next(line_iter)
    return response


def _stdout_realization(line_iter):
    response = _AceResponse({
        'INPUT': None,
        'NOTES': [],
        'WARNINGS': [],
        'ERRORS': [],
        'SENT': None,
        'RESULTS': []
    })
    results = []

    line = next(line_iter)
    while not line.startswith('NOTE: '):
        if line.startswith('WARNING: ') or line.startswith('ERROR: '):
            level, message = line.split(': ', 1)
            response['%sS' % level] = message
        else:
            results.append({'SENT': line})
        line = next(line_iter)
    response['NOTES'].append(line.split(': ', 1)[1])
    # sometimes error messages aren't prefixed with ERROR
    if line.endswith('[0 results]') and len(results) > 0:
        response['ERRORS'] = '\n'.join(d['SENT'] for d in results)
        results = []
    response['RESULTS'] = results
    return response

def _tsdb_stdout_parse(line_iter):
    response = _tsdb_stdout(line_iter)
    # two blank lines
    assert next(line_iter).strip() == ''
    assert next(line_iter).strip() == ''
    return response

def _tsdb_stdout_realization(line_iter):
    response = _tsdb_stdout(line_iter)
    # final NOTE line
    note = next(line_iter)
    assert note.startswith('NOTE: ')
    response['NOTES'].append(note.split(': ', 1)[1])
    return response    

def _tsdb_stdout(line_iter):
    response = _AceResponse({
        'INPUT': None,
        'NOTES': [],
        'WARNINGS': [],
        'ERRORS': [],
        'SENT': None,
        'RESULTS': []
    })

    line = next(line_iter)
    while (line.startswith('NOTE: ') or
           line.startswith('WARNING: ') or
           line.startswith('ERROR: ')):
        level, message = line.split(': ', 1)
        response['%sS' % level].append(message)
        line = next(line_iter)
    while line:
        expr = SExpr.parse(line)
        line = expr.remainder
        assert len(expr.data) == 2
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
                        res['DERIV'] = resval.strip()
                    elif reskey == ':mrs':
                        res['MRS'] = resval.strip()
                    elif reskey == ':surface':
                        res['SENT'] = resval.strip()
                    elif isinstance(resval, stringtypes):
                        res[reskey[1:]] = resval.strip()
                    else:
                        res[reskey[1:]] = resval
                response['RESULTS'].append(res)
        elif isinstance(val, stringtypes):
            response[key[1:]] = val.strip()
        else:
            response[key[1:]] = val
    return response

def _readlines(stream):
    """
    When ACE's stdout and stderr streams are interleaved, error messages
    can appear in the middle of, e.g., UTF-8 sequences. When decoding
    fails, remove the message (as best as possible), attach the next
    line, and try again.
    """
    msg_re = re.compile(b'(NOTE|WARNING|ERROR):.*$')
    b = stream.readline()
    while True:
        try:
            s = b.decode(encoding)
        except UnicodeDecodeError:
            m = msg_re.search(b)
            if m:
                yield b[m.start():].decode(encoding).rstrip()
                b = b[:m.start()]
                b2 = stream.readline()
                m = msg_re.match(b2)
                while m:
                    yield b2.decode(encoding).rstrip()
                b += b2
            else:
                raise
        else:
            yield s.rstrip()
            b = stream.readline()
