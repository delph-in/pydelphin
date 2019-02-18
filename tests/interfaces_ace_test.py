
import io

import pytest

from delphin.interfaces import ace

unicode = type(u'')  # temporary Python 2 hack


@pytest.fixture
def ace_mismatch():
    return unicode(
        'version mismatch: '
        'this is ACE version 0.9.29, but this grammar image '
        'was compiled by ACE version 0.9.27')


def mock_popen(pid=None, returncode=None, stdout=None, stderr=None):

    class MockedPopen():
        def __init__(self, args, **kwargs):
            self.args = args
            self.pid = pid
            self.returncode = returncode
            self.stdin = io.StringIO()
            self.stdout = stdout
            self.stderr = stderr
        def poll(self):
            return self.returncode
        def wait(self, timeout=None):
            return self.returncode
        def communicate(self, input=None, timeout=None):
            return (self.stdout.read(), self.stderr.read())
        def send_signal(self, signal):
            pass
        def terminate(self):
            pass
        def kill(self):
            pass

    return MockedPopen


def test_start(ace_mismatch, tmpdir, monkeypatch):
    popen = mock_popen(
        pid=10,
        returncode=255,
        stdout=io.StringIO(),
        stderr=io.StringIO(ace_mismatch))
    grm = tmpdir.join('grm.dat')
    grm.write('')
    with monkeypatch.context() as m:
        m.setattr(ace, 'Popen', popen)
        m.setattr(ace, '_ace_version', lambda x: (0, 9, 29))
        with pytest.raises(ace.AceProcessError):
            ace.AceParser(str(grm))
        with pytest.raises(ace.AceProcessError):
            ace.parse(str(grm), 'Dogs sleep.')
