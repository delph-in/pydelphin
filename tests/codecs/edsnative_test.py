
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


def test_decode_no_top():
    e = edsnative.decode(
        '{:\n'
        ' e2:_bark_v_1{e}[ARG1 x4]\n'
        ' _1:udef_q[BV x4]\n'
        ' x4:_dog_n_1{x}[]\n'
        '}'
    )
    assert e.top is None
    assert len(e.nodes) == 3
    # without initial colon
    e = edsnative.decode(
        '{\n'
        ' e2:_bark_v_1{e}[ARG1 x4]\n'
        ' _1:udef_q[BV x4]\n'
        ' x4:_dog_n_1{x}[]\n'
        '}'
    )
    assert e.top is None
    assert len(e.nodes) == 3
    # without newlines
    e = edsnative.decode(
        '{:e2:_bark_v_1{e}[ARG1 x4] _1:udef_q[BV x4] x4:_dog_n_1{x}[]}'
    )
    assert e.top is None
    assert len(e.nodes) == 3
    # with anonymous top (supposedly)
    e = edsnative.decode(
        '{_: e2:_bark_v_1{e}[ARG1 x4] _1:udef_q[BV x4] x4:_dog_n_1{x}[]}'
    )
    assert e.top == '_'


def test_decode_identifier():
    e = edsnative.decode(
        '#123\n'
        '{e2:\n'
        ' e2:_rain_v_1<3:9>{e SF prop, TENSE pres}[]\n'
        '}'
    )
    assert e.identifier == '123'
    e = edsnative.decode(
        '#123 {e2: e2:_rain_v_1<3:9>{e SF prop, TENSE pres}[] }'
    )
    assert e.identifier == '123'


def test_encode(dogs_bark_from_mrs):
    assert edsnative.encode(EDS()) == '{\n}'
    assert edsnative.encode(EDS(), indent=False) == '{}'
    d = EDS(**dogs_bark_from_mrs)
    assert edsnative.encode(d, indent=False) == (
        '{e2: e2:_bark_v_1{e}[ARG1 x4] _1:udef_q[BV x4] x4:_dog_n_1{x}[]}')
    assert edsnative.encode(d) == (
        '{e2:\n'
        ' e2:_bark_v_1{e}[ARG1 x4]\n'
        ' _1:udef_q[BV x4]\n'
        ' x4:_dog_n_1{x}[]\n'
        '}')


def test_encode_no_top(dogs_bark_from_mrs):
    d = EDS(**dogs_bark_from_mrs)
    d.top = None
    assert edsnative.encode(d, indent=False) == (
        '{e2:_bark_v_1{e}[ARG1 x4] _1:udef_q[BV x4] x4:_dog_n_1{x}[]}')
    assert edsnative.encode(d) == (
        '{\n'
        ' e2:_bark_v_1{e}[ARG1 x4]\n'
        ' _1:udef_q[BV x4]\n'
        ' x4:_dog_n_1{x}[]\n'
        '}')


def test_encode_identifier(dogs_bark_from_mrs):
    assert edsnative.encode(EDS(identifier='123'), indent=False) == '#123 {}'
    d = EDS(**dogs_bark_from_mrs)
    d.identifier = '123'
    assert edsnative.encode(d, indent=False) == (
        '#123 {e2: e2:_bark_v_1{e}[ARG1 x4] _1:udef_q[BV x4] x4:_dog_n_1{x}[]}'
    )
    assert edsnative.encode(d) == (
        '#123\n'
        '{e2:\n'
        ' e2:_bark_v_1{e}[ARG1 x4]\n'
        ' _1:udef_q[BV x4]\n'
        ' x4:_dog_n_1{x}[]\n'
        '}')
