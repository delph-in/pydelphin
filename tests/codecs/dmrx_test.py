
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

