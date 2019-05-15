
import pytest

from delphin.mrs import MRS, EP, HCons
from delphin.codecs import mrx


# @pytest.fixture
# def empty_mrs():
#     return MRS()


@pytest.fixture
def it_rains_mrs():
    m = MRS(
        'h0', 'e2',
        [EP('_rain_v_1', 'h1', {'ARG0': 'e2'})],
        [HCons.qeq('h0', 'h1')])
    return m


@pytest.fixture
def it_rains_mrx():
    return '\n'.join([
        '<mrs cfrom="-1" cto="-1"><label vid="0" /><var sort="e" vid="2" />',
        '<ep cfrom="-1" cto="-1"><realpred lemma="rain" pos="v" sense="1" /><label vid="1" />',
        '<fvpair><rargname>ARG0</rargname><var sort="e" vid="2" /></fvpair></ep>',
        '<hcons hreln="qeq"><hi><var sort="h" vid="0" /></hi><lo><label vid="1" /></lo></hcons>',
        '</mrs>'
    ])


@pytest.fixture
def it_rains_heavily_mrs():
    m = MRS(
        'h0', 'e2',
        [EP('_rain_v_1', 'h1', {'ARG0': 'e2'}),
         EP('_heavy_a_1', 'h1', {'ARG0': 'e3', 'ARG1': 'e2'})],
        [HCons.qeq('h0', 'h1')])
    return m


@pytest.fixture
def it_rains_heavily_mrx():
    return '\n'.join([
        '<mrs cfrom="-1" cto="-1"><label vid="0" /><var sort="e" vid="2" />',
        '<ep cfrom="-1" cto="-1"><realpred lemma="rain" pos="v" sense="1" /><label vid="1" />',
        '<fvpair><rargname>ARG0</rargname><var sort="e" vid="2" /></fvpair></ep>',
        '<ep cfrom="-1" cto="-1"><realpred lemma="heavy" pos="a" sense="1" /><label vid="1" />',
        '<fvpair><rargname>ARG0</rargname><var sort="e" vid="3" /></fvpair>',
        '<fvpair><rargname>ARG1</rargname><var sort="e" vid="2" /></fvpair></ep>',
        '<hcons hreln="qeq"><hi><var sort="h" vid="0" /></hi><lo><label vid="1" /></lo></hcons>',
        '</mrs>'
    ])


def test_encode(it_rains_mrs, it_rains_mrx,
                it_rains_heavily_mrs, it_rains_heavily_mrx):
    # assert mrx.encode(empty_mrs) == '<mrs cfrom="-1" cto="-1" />'
    # assert mrx.encode(empty_mrs, indent=True) == (
    #     '<mrs cfrom="-1" cto="-1" />')

    assert mrx.encode(it_rains_mrs) == it_rains_mrx.replace('\n', '')
    assert mrx.encode(it_rains_mrs, indent=True) == it_rains_mrx

    assert mrx.encode(it_rains_heavily_mrs, indent=True) == (
        it_rains_heavily_mrx)


def test_decode(it_rains_heavily_mrx, it_rains_heavily_mrs):
    assert mrx.decode(it_rains_heavily_mrx) == it_rains_heavily_mrs


def test_dumps(it_rains_heavily_mrs, it_rains_heavily_mrx):
    mrslist = ''.join([
        '<mrs-list>',
        it_rains_heavily_mrx.replace('\n', ''),
        '</mrs-list>'
    ])
    assert mrx.dumps([it_rains_heavily_mrs]) == mrslist


def test_loads(it_rains_heavily_mrx, it_rains_heavily_mrs):
    mrslist = '<mrs-list>' + it_rains_heavily_mrx + '</mrs-list>'
    assert mrx.loads(mrslist) == [it_rains_heavily_mrs]
