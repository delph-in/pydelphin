
import pytest

from delphin.mrs import (
    EP,
    HCons,
    MRS)


@pytest.fixture
def dogs_bark():
    return {
        'top': 'h0',
        'index': 'e2',
        'rels': [EP('_bark_v_1', 'h1',
                    args={'ARG0': 'e2', 'ARG1': 'x4'}),
                 EP('udef_q', 'h3',
                    args={'ARG0': 'x4', 'RSTR': 'h5', 'BODY': 'h7'}),
                 EP('_dog_n_1', 'h6', args={'ARG0': 'x4'})],
        'hcons': [HCons.qeq('h0', 'h1'),
                  HCons.qeq('h5', 'h6')],
        'variables': {
            'e2': {'TENSE': 'pres'},
            'x4': {'NUM': 'pl'}}}


# def test_empty_MRS():
#     m = MRS()
#     assert m.top is None
#     assert m.index is None
#     assert len(m.rels) == 0
#     assert len(m.hcons) == 0
#     assert len(m.icons) == 0
#     assert m.variables == {}


def test_basic_MRS(dogs_bark):
    m = MRS(**dogs_bark)
    assert m.top == 'h0'
    assert m.index == 'e2'
    assert len(m.rels) == 3
    assert len(m.hcons) == 2
    assert len(m.icons) == 0
    assert m.variables == {
        'h0': {},
        'h1': {},
        'e2': {'TENSE': 'pres'},
        'h3': {},
        'x4': {'NUM': 'pl'},
        'h5': {},
        'h6': {},
        'h7': {}}
