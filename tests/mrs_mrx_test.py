
import pytest

from delphin.mrs import MRS, EP, HCons
from delphin.codecs import mrx


@pytest.fixture
def it_rains_mrs():
    m = MRS(
        'h0', 'e2',
        [EP('_rain_v_1', 'h1', {'ARG0': 'e2'})],
        [HCons.qeq('h0', 'h1')])
    return m


@pytest.fixture
def it_rains_heavily_mrs():
    m = MRS(
        'h0', 'e2',
        [EP('_rain_v_1', 'h1', {'ARG0': 'e2'}),
         EP('_heavy_a_1', 'h1', {'ARG0': 'e3', 'ARG1': 'e2'})],
        [HCons.qeq('h0', 'h1')])
    return m


def test_round_trip(it_rains_mrs, it_rains_heavily_mrs):
    assert mrx.decode(mrx.encode(it_rains_mrs)) == it_rains_mrs
    assert mrx.decode(mrx.encode(it_rains_mrs, indent=True)) == it_rains_mrs
    assert mrx.decode(mrx.encode(it_rains_heavily_mrs)) == it_rains_heavily_mrs
