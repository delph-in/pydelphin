
import pytest

from delphin.lnk import Lnk
from delphin.dmrs import DMRS, Node, Link
from delphin.codecs import simpledmrs


@pytest.fixture
def it_rains_heavily_dmrs():
    d = DMRS(
        20, 10,
        nodes=[Node(10, '_rain_v_1', type='e', properties={'TENSE': 'past'}),
               Node(20, '_heavy_a_1', type='e')],
        links=[Link(20, 10, 'ARG1', 'EQ')])
    return d


@pytest.fixture
def abrams_barked_dmrs():
    d = DMRS(
        30, 30,
        nodes=[Node(10, 'udef_q'),
               Node(20, 'named', type='x',
                    carg='Abrams', lnk=Lnk.charspan(0,6)),
               Node(30, '_bark_v_1', type='e', properties={'TENSE': 'past'},
                    lnk=Lnk.charspan(7,13))],
        links=[Link(10, 20, 'RSTR', 'H'),
               Link(30, 20, 'ARG1', 'NEQ')],
        lnk=Lnk.charspan(0,14),
        surface='Abrams barked.',
        identifier='1000380')
    return d


def test_encode(it_rains_heavily_dmrs, abrams_barked_dmrs):
    assert simpledmrs.encode(DMRS()) == 'dmrs { }'

    assert simpledmrs.encode(it_rains_heavily_dmrs) == (
        'dmrs {'
        ' [top=20 index=10]'
        ' 10 [_rain_v_1 e TENSE=past];'
        ' 20 [_heavy_a_1 e];'
        ' 20:ARG1/EQ -> 10;'
        ' }')

    assert simpledmrs.encode(it_rains_heavily_dmrs, indent=True) == (
        'dmrs {\n'
        '  [top=20 index=10]\n'
        '  10 [_rain_v_1 e TENSE=past];\n'
        '  20 [_heavy_a_1 e];\n'
        '  20:ARG1/EQ -> 10;\n'
        '}')

    assert simpledmrs.encode(
        it_rains_heavily_dmrs, properties=False, indent=True) == (
            'dmrs {\n'
            '  [top=20 index=10]\n'
            '  10 [_rain_v_1 e];\n'
            '  20 [_heavy_a_1 e];\n'
            '  20:ARG1/EQ -> 10;\n'
            '}')

    assert simpledmrs.encode(abrams_barked_dmrs) == (
        'dmrs 1000380 {'
        ' [<0:14> "Abrams barked." top=30 index=30]'
        ' 10 [udef_q];'
        ' 20 [named<0:6>("Abrams") x];'
        ' 30 [_bark_v_1<7:13> e TENSE=past];'
        ' 10:RSTR/H -> 20;'
        ' 30:ARG1/NEQ -> 20;'
        ' }')

def test_decode(it_rains_heavily_dmrs):
    d = simpledmrs.decode(
        'dmrs {'
        ' [top=20 index=10]'
        ' 10 [_rain_v_1 e TENSE=past];'
        ' 20 [_heavy_a_1 e];'
        ' 20:ARG1/EQ -> 10;'
        ' }')
    assert d.top == it_rains_heavily_dmrs.top
    assert d.index == it_rains_heavily_dmrs.index
    assert d.nodes == it_rains_heavily_dmrs.nodes
    assert d.links == it_rains_heavily_dmrs.links

    d = simpledmrs.decode(
        'dmrs 1000380 {'
        ' [<0:14> "Abrams barked." top=30 index=30]'
        ' 10 [udef_q];'
        ' 20 [named<0:6>("Abrams") x];'
        ' 30 [_bark_v_1<7:13> e TENSE=past];'
        ' 10:RSTR/H -> 20;'
        ' 30:ARG1/NEQ -> 20;'
        ' }')
    assert d.cfrom == 0
    assert d.cto == 14
    assert d.surface == 'Abrams barked.'
    assert d.identifier == '1000380'
    assert d.nodes[1].carg == 'Abrams'
    assert d.nodes[1].type == 'x'
    assert d.nodes[1].cto == 6


def test_loads(it_rains_heavily_dmrs):
    ds = simpledmrs.loads(
        'dmrs {\n'
        ' [<0:18> "It rained heavily." top=20 index=10]\n'
        ' 10 [_rain_v_1<3:9> e TENSE=past];\n'
        ' 20 [_heavy_a_1<10:17> e];\n'
        ' 20:ARG1/EQ -> 10;\n'
        ' }\n'
        'dmrs {\n'
        ' [top=20 index=10]\n'
        ' 10 [_rain_v_1 e TENSE=past];\n'
        ' 20 [_heavy_a_1 e];\n'
        ' 20:ARG1/EQ -> 10;\n'
        ' }')

    assert len(ds) == 2
    assert ds[0].cto == 18
    assert ds[0].surface == 'It rained heavily.'
    assert ds[0].top == it_rains_heavily_dmrs.top
    assert ds[0].index == it_rains_heavily_dmrs.index
    assert ds[0].nodes == it_rains_heavily_dmrs.nodes
    assert ds[0].links == it_rains_heavily_dmrs.links

    assert ds[1].top == it_rains_heavily_dmrs.top
    assert ds[1].index == it_rains_heavily_dmrs.index
    assert ds[1].nodes == it_rains_heavily_dmrs.nodes
    assert ds[1].links == it_rains_heavily_dmrs.links
