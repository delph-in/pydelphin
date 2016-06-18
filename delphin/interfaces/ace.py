
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
from subprocess import (check_call, CalledProcessError, Popen, PIPE, STDOUT)

class AceProcess(object):
    """
    The base class for interfacing ACE.

    This manages most subprocess communication with ACE, but does not
    interpret the response returned via AceProcess.receive().
    Subclasses override receive() to interpret the task-specific
    response formats.
    """

    _cmdargs = []

    def __init__(self, grm, cmdargs=None, executable=None, env=None, **kwargs):
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
        self._open()

    def _open(self):
        self._p = Popen(
            [self.executable, '-g', self.grm] + self._cmdargs + self.cmdargs,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            env=self.env,
            universal_newlines=True
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
        self._p.stdin.write(datum.rstrip() + '\n')
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
        response = {
            'INPUT': None,
            'NOTES': [],
            'WARNINGS': [],
            'ERRORS': [],
            'SENT': None,
            'RESULTS': []
        }

        blank = 0

        stdout = self._p.stdout
        line = stdout.readline().rstrip()
        while True:
            if line.strip() == '':
                blank += 1
                if blank >= 2:
                    break
            elif line.startswith('SENT: ') or line.startswith('SKIP: '):
                response['SENT'] = line.split(': ', 1)[1]
            elif (line.startswith('NOTE:') or
                  line.startswith('WARNING') or
                  line.startswith('ERROR')):
                level, message = line.split(': ', 1)
                response['%sS' % level].append(message)
            else:
                mrs, deriv = line.split(' ; ')
                response['RESULTS'].append({
                    'MRS': mrs.strip(),
                    'DERIV': deriv.strip()
                })
            line = stdout.readline().rstrip()
        return response


class AceGenerator(AceProcess):
    """
    A class for managing realization requests with ACE.
    """

    _cmdargs = ['-e']

    def receive(self):
        response = {
            'INPUT': None,
            'NOTES': [],
            'WARNINGS': [],
            'ERRORS': [],
            'SENT': None,
            'RESULTS': []
        }
        results = []

        stdout = self._p.stdout
        line = stdout.readline().rstrip()
        while not line.startswith('NOTE: '):
            if line.startswith('WARNING') or line.startswith('ERROR'):
                level, message = line.split(': ', 1)
                response['%sS' % level] = message
            else:
                results.append({'SENT': line})
            line = stdout.readline().rstrip()
        # sometimes error messages aren't prefixed with ERROR
        if line.endswith('[0 results]') and len(results) > 0:
            response['ERRORS'] = '\n'.join(d['SENT'] for d in results)
            results = []
        response['RESULTS'] = results
        return response


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
