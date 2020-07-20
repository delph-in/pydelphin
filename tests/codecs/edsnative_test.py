
import pytest

from delphin.eds import EDS, Node
from delphin.codecs import eds as edsnative


@pytest.fixture
def dogs_bark_from_mrs():
    return {
        'top': 'e2',
        'nodes': [Node('e2', '_bark_v_1', type='e', edges={'ARG1': 'x4'}),
                  Node('_1', 'udef_q', edges={'BV': 'x4'}),
                  Node('x4', '_dog_n_1', type='x')]
        }


def test_decode():
    e = edsnative.decode(
        '{e2:\n'
        ' e2:_rain_v_1<3:9>{e SF prop, TENSE pres}[]\n'
        '}'
    )
    assert e.top == 'e2'
    assert len(e.nodes) == 1
    assert len(e.edges) == 0
    assert e.nodes[0].properties == {'SF': 'prop', 'TENSE': 'pres'}

    e = edsnative.decode(
        '{e2: (fragmented)\n'
        '|e5:_nearly_x_deg<0:6>[]\n'
        ' _1:_every_q<7:12>[BV x3]\n'
        ' x3:_dog_n_1<13:16>[]\n'
        ' e2:_bark_v_1<17:24>[ARG1 x3]\n'
        '}'
    )
    assert e.top == 'e2'
    assert len(e.nodes) == 4
    assert len(e.edges) == 2
    assert e.nodes[3].predicate == '_bark_v_1'


def test_encode(dogs_bark_from_mrs):
    d = EDS(**dogs_bark_from_mrs)
    assert edsnative.encode(d) == (
        '{e2: e2:_bark_v_1{e}[ARG1 x4] _1:udef_q[BV x4] x4:_dog_n_1{x}[]}')
    assert edsnative.encode(d, indent=True) == (
        '{e2:\n'
        ' e2:_bark_v_1{e}[ARG1 x4]\n'
        ' _1:udef_q[BV x4]\n'
        ' x4:_dog_n_1{x}[]\n'
        '}')
