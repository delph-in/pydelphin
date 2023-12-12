
import pytest

from delphin.codecs import dmrx
from delphin.dmrs import DMRS, Node


@pytest.fixture
def empty_dmrs():
    return DMRS()


@pytest.fixture
def it_rains_dmrs():
    d = DMRS(
        10, 10,
        nodes=[Node(10, '_rain_v_1', 'e', {'TENSE': 'pres'})],
        links=[])
    return d


def test_round_trip(empty_dmrs, it_rains_dmrs):
    assert dmrx.decode(dmrx.encode(empty_dmrs)) == empty_dmrs
    assert dmrx.decode(dmrx.encode(empty_dmrs, indent=True)) == empty_dmrs

    assert dmrx.decode(dmrx.encode(it_rains_dmrs)) == it_rains_dmrs
    assert dmrx.decode(dmrx.encode(it_rains_dmrs)) == it_rains_dmrs


def test_no_properties(it_rains_dmrs):
    d = dmrx.decode(dmrx.encode(it_rains_dmrs))
    assert d.nodes[0].properties == {'TENSE': 'pres'}
    d = dmrx.decode(dmrx.encode(it_rains_dmrs, properties=False))
    assert d.nodes[0].properties == {}


def test_case_sensitivity_issue_333(it_rains_dmrs):
    # https://github.com/delph-in/pydelphin/issues/333
    s = dmrx.encode(it_rains_dmrs)
    assert 'tense="pres"' in s
    d = dmrx.decode(
        '<dmrs-list>'
        '<dmrs cfrom="-1" cto="-1" top="10" index="10">'
        '<node nodeid="10" cfrom="-1" cto="-1">'
        '<realpred lemma="RAIN" pos="v" sense="1" />'
        '<sortinfo tense="PRES" cvarsort="E" />'
        '</node></dmrs></dmrs-list>'
    )
    assert d.nodes[0].predicate == '_rain_v_1'
    assert d.nodes[0].type == 'e'
    assert d.nodes[0].properties == {'TENSE': 'pres'}
