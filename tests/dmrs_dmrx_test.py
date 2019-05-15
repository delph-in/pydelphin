
import pytest

from delphin.dmrs import DMRS, Node, Link
from delphin.codecs import dmrx


@pytest.fixture
def empty_dmrs():
    return DMRS()


@pytest.fixture
def it_rains_dmrs():
    d = DMRS(
        10, 10,
        nodes=[Node(10, '_rain_v_1', 'e')],
        links=[])
    return d


@pytest.fixture
def it_rains_dmrx():
    return (
        '<dmrs cfrom="-1" cto="-1" index="10" top="10">\n'
        '  <node cfrom="-1" cto="-1" nodeid="10">\n'
        '    <realpred lemma="rain" pos="v" sense="1" />\n'
        '    <sortinfo cvarsort="e" />\n'
        '  </node>\n'
        '</dmrs>')


@pytest.fixture
def it_rains_heavily_dmrs():
    d = DMRS(
        20, 10,
        nodes=[Node(10, '_rain_v_1', type='e'),
               Node(20, '_heavy_a_1', type='e')],
        links=[Link(20, 10, 'ARG1', 'EQ')])
    return d


@pytest.fixture
def it_rains_heavily_dmrx():
    return (
        '<dmrs cfrom="-1" cto="-1" index="10" top="20">\n'
        '  <node cfrom="-1" cto="-1" nodeid="10">\n'
        '    <realpred lemma="rain" pos="v" sense="1" />\n'
        '    <sortinfo cvarsort="e" />\n'
        '  </node>\n'
        '  <node cfrom="-1" cto="-1" nodeid="20">\n'
        '    <realpred lemma="heavy" pos="a" sense="1" />\n'
        '    <sortinfo cvarsort="e" />\n'
        '  </node>\n'
        '  <link from="20" to="10">\n'
        '    <rargname>ARG1</rargname>\n'
        '    <post>EQ</post>\n'
        '  </link>\n'
        '</dmrs>')


def test_encode(empty_dmrs, it_rains_dmrs, it_rains_dmrx,
                it_rains_heavily_dmrs, it_rains_heavily_dmrx):
    assert dmrx.encode(empty_dmrs) == '<dmrs cfrom="-1" cto="-1" />'
    assert dmrx.encode(empty_dmrs, indent=True) == (
        '<dmrs cfrom="-1" cto="-1" />')

    assert dmrx.encode(it_rains_dmrs) == (
        '<dmrs cfrom="-1" cto="-1" index="10" top="10">'
        '<node cfrom="-1" cto="-1" nodeid="10">'
        '<realpred lemma="rain" pos="v" sense="1" />'
        '<sortinfo cvarsort="e" />'
        '</node>'
        '</dmrs>')
    assert dmrx.encode(it_rains_dmrs, indent=True) == (
        '<dmrs cfrom="-1" cto="-1" index="10" top="10">\n'
        '<node cfrom="-1" cto="-1" nodeid="10">'
        '<realpred lemma="rain" pos="v" sense="1" />'
        '<sortinfo cvarsort="e" />'
        '</node>\n'
        '</dmrs>')
    assert dmrx.encode(it_rains_dmrs, indent=2) == it_rains_dmrx

    assert dmrx.encode(it_rains_heavily_dmrs, indent=2) == (
        it_rains_heavily_dmrx)


def test_decode(it_rains_heavily_dmrx):
    dmrx.decode(it_rains_heavily_dmrx)


def test_dumps(it_rains_heavily_dmrs):
    dmrx.dumps([it_rains_heavily_dmrs])


def test_loads(it_rains_heavily_dmrx):
    dmrx.loads('<dmrs-list>' + it_rains_heavily_dmrx + '</dmrs-list>')
