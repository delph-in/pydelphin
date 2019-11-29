# -*- coding: utf-8 -*-

"""
Deserialization of MRSs in ACE's stdout protocols.
"""

from pathlib import Path

from delphin.codecs import simplemrs
from delphin.util import SExpr


CODEC_INFO = {
    'representation': 'mrs',
}


def load(source):
    """
    Deserialize SimpleMRSs from ACE parsing output (handle or filename)

    Args:
        source (str, file): ACE parsing output as a filename or handle
    Returns:
        a list of MRS objects
    """
    if hasattr(source, 'read'):
        ms = list(_decode(source))
    else:
        source = Path(source).expanduser()
        with source.open() as fh:
            ms = list(_decode(fh))
    return ms


def loads(s):
    """
    Deserialize SimpleMRSs from ACE parsing output (as a string)

    Args:
        s (str): ACE parsing output as a string
    Returns:
        a list of MRS objects
    """
    if hasattr(s, 'decode'):
        s = s.decode('utf-8')
    ms = list(_decode(s.splitlines()))
    return ms


def decode(s):
    """
    Deserialize an MRS object from a SimpleMRS string.
    """
    if hasattr(s, 'decode'):
        s = s.decode('utf-8')
    ms = next(_decode(s.splitlines()))
    return ms


# read simplemrs from ACE output

def _decode(lines):
    surface = None
    newline = False
    for line in lines:
        if line.startswith('SENT: '):
            surface = line[6:].rstrip()
        # regular ACE output
        elif line.startswith('['):
            m = line.partition(' ;  ')[0].strip()
            m = simplemrs.decode(m)
            m.surface = surface
            yield m
        # with --tsdb-stdout
        elif line.startswith('('):
            while line:
                data, remainder = SExpr.parse(line)
                line = remainder.lstrip()
                if len(data) == 2 and data[0] == ':results':
                    for result in data[1]:
                        for key, val in result:
                            if key == ':mrs':
                                yield simplemrs.decode(val)
        elif line == '\n':
            if newline:
                surface = None
                newline = False
            else:
                newline = True
        else:
            pass
