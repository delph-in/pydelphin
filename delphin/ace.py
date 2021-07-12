
"""
An interface for the ACE processor.
"""

from typing import (
    Any, Iterator, Iterable, Mapping, Dict, List, Tuple, Pattern, IO)
import logging
import os
from pathlib import Path
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
import locale

from delphin import interface
from delphin import util
from delphin.exceptions import PyDelphinException
# Default modules need to import the PyDelphin version
from delphin.__about__ import __version__  # noqa: F401


logger = logging.getLogger(__name__)


# do this right away to avoid some encoding issues
locale.setlocale(locale.LC_ALL, '')
encoding = locale.getpreferredencoding(False)


class ACEProcessError(PyDelphinException):
    """Raised when the ACE process has crashed and cannot be recovered."""


class ACEProcess(interface.Processor):
    """
    The base class for interfacing ACE.

    This manages most subprocess communication with ACE, but does not
    interpret the response returned via ACE's stdout. Subclasses
    override the :meth:`receive` method to interpret the task-specific
    response formats.

    Note that not all arguments to this class are used by every
    subclass; the documentation for each subclass specifies which are
    available.

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
        full_forest (bool): if `True` and *tsdbinfo* is `True`, output
            the full chart for each parse result
        stderr (file): stream used for ACE's stderr
    """

    _cmdargs: List[str] = []
    _termini: List[Pattern[str]] = []

    def __init__(self,
                 grm: util.PathLike,
                 cmdargs: List[str] = None,
                 executable: util.PathLike = None,
                 env: Mapping[str, str] = None,
                 tsdbinfo: bool = True,
                 full_forest: bool = False,
                 stderr: IO[Any] = None):
        self.grm = str(Path(grm).expanduser())

        self.cmdargs = cmdargs or []
        # validate the arguments
        _ace_argparser.parse_args(self.cmdargs)

        self.executable = 'ace'
        if executable:
            self.executable = str(Path(executable).expanduser())

        ace_version = self.ace_version
        if ace_version >= (0, 9, 14):
            self.cmdargs.append('--tsdb-notes')
        if tsdbinfo and ace_version >= (0, 9, 24):
            self.cmdargs.extend(['--tsdb-stdout', '--report-labels'])
            setattr(self, 'receive', self._tsdb_receive)
            if full_forest:
                self._cmdargs.append('--itsdb-forest')
        else:
            setattr(self, 'receive', self._default_receive)
        self.env = env or os.environ
        self._run_id = -1
        self.run_infos: List[Dict[str, Any]] = []
        self._stderr = stderr
        self._open()

    @property
    def ace_version(self) -> Tuple[int, ...]:
        """The version of the specified ACE binary."""
        return _ace_version(self.executable)

    @property
    def run_info(self) -> Dict[str, Any]:
        """Contextual information about the the running process."""
        return self.run_infos[-1]

    def _open(self) -> None:
        self._p = Popen(
            [self.executable, '-g', self.grm] + self._cmdargs + self.cmdargs,
            stdin=PIPE,
            stdout=PIPE,
            stderr=self._stderr,
            env=self.env,
            universal_newlines=True
        )
        self._run_id += 1
        self.run_infos.append({
            'run-id': self._run_id,
            'application': 'ACE {} via PyDelphin v{}'.format(
                '.'.join(map(str, self.ace_version)), __version__),
            'environment': ' '.join(self.cmdargs),
            'user': getuser(),
            'host': gethostname(),
            'os': platform(),
            'start': datetime.now()
        })
        if self._p.poll() is not None and self._p.returncode != 0:
            raise ACEProcessError("ACE process closed on startup")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False  # don't try to handle any exceptions

    def _result_lines(self, termini: List[Pattern[str]] = None) -> List[str]:
        poll = self._p.poll
        assert self._p.stdout is not None, 'cannot receive output from ACE'
        next_line = self._p.stdout.readline

        if termini is None:
            termini = self._termini
        i, end = 0, len(termini)
        cur_terminus = termini[i]

        lines = []
        while i < end:
            s = next_line()
            if s == '' and poll() is not None:
                logger.info(
                    'Process closed unexpectedly; giving up.'
                )
                self.close()
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

    def _read_run_info(self, line: str) -> None:
        assert line.startswith('NOTE: tsdb run:')
        for key, value in _sexpr_data(line[15:].lstrip()):
            if key == ':application':
                continue  # PyDelphin sets 'application'
            self.run_info[key.lstrip(':')] = value

    def send(self, datum: str) -> None:
        """
        Send *datum* (e.g. a sentence or MRS) to ACE.

        Warning:
          Sending data without reading (e.g., via :meth:`receive`) can
          fill the buffer and cause data to be lost. Use the
          :meth:`interact` method for most data-processing tasks with
          ACE.
        """
        assert self._p.stdin is not None, 'cannot send inputs to ACE'
        try:
            self._p.stdin.write((datum.rstrip() + '\n'))
            self._p.stdin.flush()
        except (IOError, OSError):  # ValueError if file was closed manually
            logger.info(
                'Attempted to write to a closed process; attempting to reopen'
            )
            self._open()
            self._p.stdin.write((datum.rstrip() + '\n'))
            self._p.stdin.flush()

    def receive(self) -> interface.Response:
        """
        Return the stdout response from ACE.

        Warning:
            Reading beyond the last line of stdout from ACE can cause
            the process to hang while it waits for the next line. Use
            the :meth:`interact` method for most data-processing tasks
            with ACE.
        """
        raise NotImplementedError()

    def _default_receive(self) -> interface.Response:
        raise NotImplementedError()

    def _tsdb_receive(self) -> interface.Response:
        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)
        # now it should be safe to reopen a closed process (if necessary)
        if self._p.poll() is not None:
            logger.info('Attempting to restart ACE.')
            self._open()
        line = ' '.join(lines)  # ACE 0.9.24 on Mac puts superfluous newlines
        response = _tsdb_response(response, line)
        return response

    def interact(self, datum: str) -> interface.Response:
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
            :class:`~delphin.interface.Response`
        """
        validated = self._validate_input(datum)
        if validated:
            self.send(validated)
            result = self.receive()
        else:
            result, lines = _make_response(
                [('NOTE: PyDelphin could not validate the input and '
                  'refused to send it to ACE'),
                 f'SKIP: {datum}'],
                self.run_info)
        result['input'] = datum
        return result

    def process_item(self,
                     datum: str,
                     keys: Dict[str, Any] = None) -> interface.Response:
        """
        Send *datum* to ACE and return the response with context.

        The *keys* parameter can be used to track item identifiers
        through an ACE interaction. If the `task` member is set on
        the ACEProcess instance (or one of its subclasses), it is
        kept in the response as well.
        Args:
            datum (str): the input sentence or MRS
            keys (dict): a mapping of item identifier names and values
        Returns:
            :class:`~delphin.interface.Response`
        """
        response = self.interact(datum)
        if keys is not None:
            response['keys'] = keys
        if 'task' not in response and self.task is not None:
            response['task'] = self.task
        return response

    def close(self) -> int:
        """
        Close the ACE process and return the process's exit code.
        """
        self.run_info['end'] = datetime.now()
        if self._p.stdin is not None:
            self._p.stdin.close()
        if self._p.stdout is not None:
            for line in self._p.stdout:
                if line.startswith('NOTE: tsdb run:'):
                    self._read_run_info(line)
                else:
                    logger.debug('ACE cleanup: %s', line.rstrip())
        retval = self._p.wait()
        return retval

    def _validate_input(self, datum: str) -> str:
        raise NotImplementedError()


class ACEParser(ACEProcess):
    """
    A class for managing parse requests with ACE.

    See :class:`ACEProcess` for initialization parameters.
    """

    task = 'parse'
    _termini = [re.compile(r'^$'), re.compile(r'^$')]

    def _validate_input(self, datum: str):
        # valid input for parsing is non-empty
        # (this relies on an empty string evaluating to False)
        return isinstance(datum, str) and datum.strip()

    def _default_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)
        response['results'] = [
            dict(zip(('mrs', 'derivation'), map(str.strip, line.split(' ; '))))
            for line in lines
        ]
        return response


class ACETransferer(ACEProcess):
    """
    A class for managing transfer requests with ACE.

    See :class:`ACEProcess` for initialization parameters.
    """

    task = 'transfer'
    _termini = [re.compile(r'^$')]

    def __init__(self,
                 grm: util.PathLike,
                 cmdargs: List[str] = None,
                 executable: util.PathLike = None,
                 env: Mapping[str, str] = None,
                 stderr: IO[Any] = None):
        super().__init__(grm, cmdargs=cmdargs, executable=executable, env=env,
                         tsdbinfo=False, full_forest=False, stderr=stderr)

    def _validate_input(self, datum):
        return _possible_mrs(datum)

    def _default_receive(self):
        lines = self._result_lines()
        response, lines = _make_response(lines, self.run_info)
        response['results'] = [{'mrs': line.strip()} for line in lines]
        return response


class ACEGenerator(ACEProcess):
    """
    A class for managing realization requests with ACE.

    See :class:`ACEProcess` for initialization parameters.
    """

    task = 'generate'
    _cmdargs = ['-e', '--tsdb-notes']
    _termini = [re.compile(r'NOTE: tsdb parse: ')]

    def __init__(self,
                 grm: util.PathLike,
                 cmdargs: List[str] = None,
                 executable: util.PathLike = None,
                 env: Mapping[str, str] = None,
                 tsdbinfo: bool = True,
                 stderr: IO[Any] = None):
        super().__init__(grm, cmdargs=cmdargs, executable=executable, env=env,
                         tsdbinfo=tsdbinfo, full_forest=False, stderr=stderr)

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


def compile(cfg_path: util.PathLike,
            out_path: util.PathLike,
            executable: util.PathLike = None,
            env: Mapping[str, str] = None,
            stdout: IO[Any] = None,
            stderr: IO[Any] = None) -> None:
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
        stdout (file, optional): stream used for ACE's stdout
        stderr (file, optional): stream used for ACE's stderr
    """
    cfg_path = str(Path(cfg_path).expanduser())
    out_path = str(Path(out_path).expanduser())
    try:
        check_call(
            [(executable or 'ace'), '-g', cfg_path, '-G', out_path],
            stdout=stdout, stderr=stderr, close_fds=True,
            env=(env or os.environ)
        )
    except (CalledProcessError, OSError):
        logger.error(
            'Failed to compile grammar with ACE. See %s',
            getattr(stderr, 'name', '<stderr>')
        )
        raise


def parse_from_iterable(
        grm: util.PathLike,
        data: Iterable[str],
        **kwargs: Any) -> Iterator[interface.Response]:
    """
    Parse each sentence in *data* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        data (iterable): the sentences to parse
        **kwargs: additional keyword arguments to pass to the ACEParser
    Yields:
        :class:`~delphin.interface.Response`
    Example:
        >>> sentences = ['Dogs bark.', 'It rained']
        >>> responses = list(ace.parse_from_iterable('erg.dat', sentences))
        NOTE: parsed 2 / 2 sentences, avg 723k, time 0.01026s
    """
    with ACEParser(grm, **kwargs) as parser:
        for datum in data:
            yield parser.interact(datum)


def parse(grm: util.PathLike,
          datum: str,
          **kwargs: Any) -> interface.Response:
    """
    Parse sentence *datum* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        datum (str): the sentence to parse
        **kwargs: additional keyword arguments to pass to the ACEParser
    Returns:
        :class:`~delphin.interface.Response`
    Example:
        >>> response = ace.parse('erg.dat', 'Dogs bark.')
        NOTE: parsed 1 / 1 sentences, avg 797k, time 0.00707s
    """
    return next(parse_from_iterable(grm, [datum], **kwargs))


def transfer_from_iterable(
        grm: util.PathLike,
        data: Iterable[str],
        **kwargs: Any) -> Iterator[interface.Response]:
    """
    Transfer from each MRS in *data* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        data (iterable): source MRSs as SimpleMRS strings
        **kwargs: additional keyword arguments to pass to the
            ACETransferer
    Yields:
        :class:`~delphin.interface.Response`
    """
    with ACETransferer(grm, **kwargs) as transferer:
        for datum in data:
            yield transferer.interact(datum)


def transfer(grm: util.PathLike,
             datum: str,
             **kwargs: Any) -> interface.Response:
    """
    Transfer from the MRS *datum* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        datum: source MRS as a SimpleMRS string
        **kwargs: additional keyword arguments to pass to the
            ACETransferer
    Returns:
        :class:`~delphin.interface.Response`
    """
    return next(transfer_from_iterable(grm, [datum], **kwargs))


def generate_from_iterable(
        grm: util.PathLike,
        data: Iterable[str],
        **kwargs: Any) -> Iterator[interface.Response]:
    """
    Generate from each MRS in *data* with ACE using grammar *grm*.

    Args:
        grm (str): path to a compiled grammar image
        data (iterable): MRSs as SimpleMRS strings
        **kwargs: additional keyword arguments to pass to the
            ACEGenerator
    Yields:
        :class:`~delphin.interface.Response`
    """
    with ACEGenerator(grm, **kwargs) as generator:
        for datum in data:
            yield generator.interact(datum)


def generate(grm: util.PathLike,
             datum: str,
             **kwargs: Any) -> interface.Response:
    """
    Generate from the MRS *datum* with ACE using *grm*.

    Args:
        grm (str): path to a compiled grammar image
        datum: the SimpleMRS string to generate from
        **kwargs: additional keyword arguments to pass to the
            ACEGenerator
    Returns:
        :class:`~delphin.interface.Response`
    """
    return next(generate_from_iterable(grm, [datum], **kwargs))


# The following defines the command-line options available for users to
# specify in ACEProcess tasks. For a description of these options, see:
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
_ace_argparser.add_argument('--udx', nargs='?', choices=('all',))
_ace_argparser.add_argument('--yy-rules', action='store_true')
_ace_argparser.add_argument('--max-words', type=int)


def _ace_version(executable: str) -> Tuple[int, ...]:
    # 0.9.0 is the initial public release of ACE
    version: Tuple[int, ...] = (0, 9, 0)
    try:
        out = check_output([executable, '-V'], universal_newlines=True)
    except (CalledProcessError, OSError):
        logger.error('Failed to get ACE version number.')
        raise
    else:
        match = re.search(r'ACE version ([.0-9]+)', out)
        if match is not None:
            version = tuple(map(int, match.group(1).split('.')))
    return version


def _possible_mrs(s: str) -> str:
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
            logger.debug('Possible MRS found at <%d:%d>: %s', start, end, s)
            s = s[start:end]
        return s
    else:
        return ''


def _make_response(lines, run) -> Tuple[interface.Response, List[str]]:
    response = interface.Response({
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


def _sexpr_data(line: str) -> Iterator[Tuple[str, Any]]:
    while line:
        try:
            expr = util.SExpr.parse(line)
        except IndexError:
            expr = util.SExprResult(
                (':error', 'incomplete output from ACE'),
                '')
        if len(expr.data) != 2:
            logger.error('Could not read output from ACE: %s', line)
            break

        key, val = expr.data
        assert isinstance(key, str)
        yield key, val

        line = expr.remainder.lstrip()


def _tsdb_response(response: interface.Response,
                   line: str) -> interface.Response:
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
                    elif isinstance(resval, str):
                        res[reskey[1:]] = resval.strip()
                    else:
                        res[reskey[1:]] = resval
                response['results'].append(res)
        elif key == ':chart':
            response['chart'] = chart = []
            for edge in val:
                chart.append({edgekey[1:]: edgeval
                              for edgekey, edgeval in edge})
        elif isinstance(val, str):
            response[key[1:]] = val.strip()
        else:
            response[key[1:]] = val
    return response
