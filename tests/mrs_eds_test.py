
import pytest

from delphin.mrs import simplemrs, eds
from delphin.mrs.components import Node, Pred, Lnk
from delphin.mrs.config import CVARSORT

# empty
empty = simplemrs.loads_one('''[ ]''')

# "It rains."
it_rains = simplemrs.loads_one('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ "_rain_v_1_rel"<3:9> LBL: h1 ARG0: e2 ] >
  HCONS: < h0 qeq h1 > ]
''')

dogs_chase_Kim = simplemrs.loads_one('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ udef_q_rel<0:4> LBL: h4 ARG0: x3 RSTR: h5 BODY: h6 ]
    [ _dog_n_1_rel<0:4> LBL: h7 ARG0: x3 [ x PERS: 3 NUM: pl IND: + ] ]
    [ _chase_v_1_rel<5:10> LBL: h1 ARG0: e2 ARG1: x3 ARG2: x8 ]
    [ proper_q<11:15> LBL: h9 ARG0: x8 RSTR: h10 BODY: h11 ]
    [ named_rel<11:15> LBL: h12 ARG0: x8 [ x PERS: 3 NUM: sg IND: + ] CARG: "Kim" ] >
  HCONS: < h0 qeq h1 h5 qeq h7 h10 qeq h12 > ]
''')

# example from Jacy with duplicate ARG0s
kotaenakatta = simplemrs.loads_one('''
[ TOP: h0
  INDEX: e2 [ e TENSE: past MOOD: indicative PROG: - PERF: - ASPECT: default_aspect PASS: - SF: prop ]
  RELS: < [ "_kotaeru_v_3_rel"<0:2> LBL: h4 ARG0: e2 ARG1: i3 ]
          [ "_neg_v_rel"<3:6> LBL: h1 ARG0: e2 ARG1: h5 ] >
  HCONS: < h0 qeq h1 h5 qeq h4 > ]
'''
)

nearly_every_dog_barked = simplemrs.loads_one('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: past MOOD: indicative PROG: - PERF: - ]
  RELS: < [ _nearly_x_deg_rel<0:6> LBL: h4 ARG0: e5 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: u6 ]
    [ _every_q_rel<7:12> LBL: h4 ARG0: x3 RSTR: h7 BODY: h8 ]
    [ _dog_n_1_rel<13:16> LBL: h9 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] ]
    [ _bark_v_1_rel<17:24> LBL: h1 ARG0: e2 ARG1: x3 ] >
  HCONS: < h0 qeq h1 h7 qeq h9 > ]
'''
)

# ltop different from index
kim_probably_sleeps = simplemrs.loads_one('''
[ LTOP: h0
  INDEX: e2 [ e SF: prop TENSE: pres MOOD: indicative PROG: - PERF: - ]
  RELS: < [ proper_q<0:3> LBL: h4 ARG0: x3 [ x PERS: 3 NUM: sg IND: + ] RSTR: h5 BODY: h6 ]
    [ named<0:3> LBL: h7 CARG: "Kim" ARG0: x3 ]
    [ _probable_a_1<4:12> LBL: h1 ARG0: e9 [ e SF: prop TENSE: untensed MOOD: indicative PROG: - PERF: - ] ARG1: h10 ]
    [ _sleep_v_1<13:20> LBL: h11 ARG0: e2 ARG1: x3 ] >
  HCONS: < h0 qeq h1 h5 qeq h7 h10 qeq h11 > ]
''')

@pytest.fixture
def eds_empty():
    return eds.Eds()

@pytest.fixture
def eds_it_rains():
    return eds.Eds(
        top='e2',
        nodes=[
            Node(
                'e2',
                Pred.surface('"_rain_v_1_rel"'),
                sortinfo={
                    'SF': 'prop', 'TENSE': 'pres', 'MOOD': 'indicative',
                    'PROG': '-', 'PERF': '-', CVARSORT: 'e'},
                lnk=Lnk.charspan(3, 9)
            )
        ],
        edges=[]
    )

@pytest.fixture
def eds_dogs_chase_Kim():
    return eds.Eds(
        top='e2',
        nodes=[
            Node('_1', Pred.surface('udef_q_rel')),
            Node('x4', Pred.surface('"_dog_n_1_rel"')),
            Node('e2', Pred.surface('"_chase_v_1_rel"')),
            Node('_2', Pred.surface('proper_q_rel')),
            Node('x6', Pred.surface('named_rel'), carg='Kim')
        ],
        edges=[
            ('_1', 'BV', 'x4'),
            ('_2', 'BV', 'x6'),
            ('e2', 'ARG1', 'x4'),
            ('e2', 'ARG2', 'x6')
        ]
    )

@pytest.fixture
def eds_kim_probably_sleeps():
    return eds.Eds(
        top='e9',
        nodes=[
            Node('_1', Pred.surface('proper_q_rel')),
            Node('x3', Pred.surface('named_rel'), carg='Kim'),
            Node('e9', Pred.surface('_probable_a_1_rel')),
            Node('e2', Pred.surface('_sleep_v_1_rel')),
        ],
        edges=[
            ('_1', 'BV', 'x3'),
            ('e9', 'ARG1', 'e2'),
            ('e2', 'ARG1', 'x3')
        ]
    )

class TestEds(object):
    def test_init(self, eds_empty, eds_it_rains, eds_dogs_chase_Kim, eds_kim_probably_sleeps):
        assert eds_empty.top is None
        assert len(eds_empty.nodes()) == 0

        assert eds_it_rains.top == 'e2'
        assert len(eds_it_rains.nodes()) == 1
        assert eds_it_rains.node('e2').pred == '"_rain_v_1_rel"'
        assert len(eds_it_rains.edges('e2')) == 0

        assert eds_dogs_chase_Kim.top == 'e2'
        assert len(eds_dogs_chase_Kim.nodes()) == 5
        assert eds_dogs_chase_Kim.nodeids() == ['_1', 'x4', 'e2', '_2', 'x6']
        assert eds_dogs_chase_Kim.node('e2').pred == '"_chase_v_1_rel"'
        assert eds_dogs_chase_Kim.edges('e2') == {'ARG1': 'x4', 'ARG2': 'x6'}
        assert eds_dogs_chase_Kim.node('x6').carg == 'Kim'

        assert eds_kim_probably_sleeps.top == 'e9'
        assert len(eds_kim_probably_sleeps.nodes()) == 4
        assert eds_kim_probably_sleeps.nodeids() == ['_1', 'x3', 'e9', 'e2']
        assert eds_kim_probably_sleeps.node('e2').pred == '"_sleep_v_1_rel"'
        assert eds_kim_probably_sleeps.edges('e2') == {'ARG1': 'x3'}
        assert eds_kim_probably_sleeps.node('x3').carg == 'Kim'

    def test_to_dict(self, eds_empty, eds_it_rains, eds_dogs_chase_Kim, eds_kim_probably_sleeps):
        assert eds_empty.to_dict() == {'top': None, 'nodes': {}}

        assert eds_it_rains.to_dict() == {
            'top': 'e2',
            'nodes': {
                'e2': {
                    'label': '_rain_v_1',
                    'lnk': {'from': 3, 'to': 9},
                    'properties': {
                        'SF': 'prop', 'TENSE': 'pres', 'MOOD': 'indicative',
                        'PROG': '-', 'PERF': '-'
                    },
                    'type': 'e',
                    'edges': {}
                }
            }
        }
        assert eds_it_rains.to_dict(properties=False) == {
            'top': 'e2',
            'nodes': {
                'e2': {
                    'label': '_rain_v_1',
                    'lnk': {'from': 3, 'to': 9},
                    'edges': {}
                }
            }
        }

        assert eds_dogs_chase_Kim.to_dict() == {
            'top': 'e2',
            'nodes': {
                '_1': {'label': 'udef_q', 'edges': {'BV': 'x4'}},
                'x4': {'label': '_dog_n_1', 'edges': {}},
                'e2': {'label': '_chase_v_1',
                       'edges': {'ARG1': 'x4', 'ARG2': 'x6'}},
                '_2': {'label': 'proper_q', 'edges': {'BV': 'x6'}},
                'x6': {'label': 'named', 'edges': {}, 'carg': 'Kim'}
            }
        }

        assert eds_kim_probably_sleeps.to_dict() == {
            'top': 'e9',
            'nodes': {
                '_1': {'label': 'proper_q', 'edges': {'BV': 'x3'}},
                'x3': {'label': 'named', 'edges': {}, 'carg': 'Kim'},
                'e9': {'label': '_probable_a_1', 'edges': {'ARG1': 'e2'}},
                'e2': {'label': '_sleep_v_1', 'edges': {'ARG1': 'x3'}},
            }
        }


def test_deserialize():
    e = eds.loads_one('{}')
    assert e.top is None
    assert len(e.nodes()) == 0

    e = eds.loads_one('{:}')
    assert e.top is None
    assert len(e.nodes()) == 0

    e = eds.loads_one('{e2: e2:_rain_v_1<3:9>[]}')
    assert e.top == 'e2'
    assert len(e.nodes()) == 1
    assert e.nodes()[0].pred == '_rain_v_1_rel'

    e = eds.loads_one('{: e2:_rain_v_1<3:9>[]}')
    assert e.top is None
    assert len(e.nodes()) == 1
    assert e.nodes()[0].pred == '_rain_v_1_rel'

    e = eds.loads_one(
        '{e2:\n'
        ' e2:_rain_v_1<3:9>{e SF prop, TENSE pres}[]\n'
        '}'
    )
    assert e.top == 'e2'
    assert len(e.nodes()) == 1
    assert e.nodes()[0].properties == {'SF': 'prop', 'TENSE': 'pres'}

    e = eds.loads_one(
        '{e2: (fragmented)\n'
        '|e5:_nearly_x_deg<0:6>[]\n'
        ' _1:_every_q<7:12>[BV x3]\n'
        ' x3:_dog_n_1<13:16>[]\n'
        ' e2:_bark_v_1<17:24>[ARG1 x3]\n'
        '}'
    )
    assert e.top == 'e2'
    assert len(e.nodes()) == 4

    # GitHub issue #203
    # _thing_n_of-about was tripping up the parser due to the hyphen,
    # and the empty property list of _business_n_1 does not have a space
    # before } (without the space is better, I think)
    e = eds.loads_one(
        '{e3:\n'
        ' _1:udef_q<0:35>[BV x6]\n'
        ' e9:_successful_a_1<0:10>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x6]\n'
        ' e10:_american_a_1<11:19>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x6]\n'
        ' e12:compound<20:35>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x6, ARG2 x11]\n'
        ' _2:udef_q<20:28>[BV x11]\n'
        ' x11:_business_n_1<20:28>{x}[]\n'
        ' x6:_owner_n_of<29:35>{x PERS 3, NUM pl, IND +}[]\n'
        ' e3:_do_v_1<36:38>{e SF prop, TENSE pres, MOOD indicative, PROG -, PERF -}[ARG1 x6, ARG2 x18]\n'
        ' _3:_the_q<39:42>[BV x18]\n'
        ' e23:_same_a_as<43:47>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 x18]\n'
        ' e25:comp_equal<43:47>{e SF prop, TENSE untensed, MOOD indicative, PROG -, PERF -}[ARG1 e23]\n'
        ' x18:_thing_n_of-about<48:54>{x PERS 3, NUM sg, IND +}[]\n'
        '}'
    )
    assert e.top == 'e3'
    assert len(e.nodes()) == 12
    assert e.nodes()[5].properties == {}
    assert e.nodes()[11].pred == '_thing_n_of-about'


def test_serialize():
    assert eds.dumps_one(empty, pretty_print=False) == '{:}'
    assert eds.dumps_one(empty, pretty_print=True) == '{:\n}'
    assert eds.dumps_one(empty) == '{:\n}'  # default pretty-print

    assert eds.dumps_one(it_rains) == (
        '{e2:\n'
        ' e2:_rain_v_1<3:9>[]\n'
        '}'
    )
    assert eds.dumps_one(it_rains, properties=True) == (
        '{e2:\n'
        ' e2:_rain_v_1<3:9>{e MOOD indicative, PERF -, PROG -, SF prop, TENSE pres}[]\n'
        '}'
    )

    assert eds.dumps_one(dogs_chase_Kim) == (
        '{e2:\n'
        ' _1:udef_q<0:4>[BV x3]\n'
        ' x3:_dog_n_1<0:4>[]\n'
        ' e2:_chase_v_1<5:10>[ARG1 x3, ARG2 x8]\n'
        ' _2:proper_q<11:15>[BV x8]\n'
        ' x8:named<11:15>("Kim")[]\n'
        '}'
    )

    assert eds.dumps_one(kotaenakatta) == (
        '{_1:\n'
        ' e2:_kotaeru_v_3<0:2>[]\n'
        ' _1:_neg_v<3:6>[ARG1 e2]\n'
        '}'
    )

    assert eds.dumps_one(nearly_every_dog_barked) == (
        '{e2:\n'
        ' e5:_nearly_x_deg<0:6>[]\n'
        ' _1:_every_q<7:12>[BV x3]\n'
        ' x3:_dog_n_1<13:16>[]\n'
        ' e2:_bark_v_1<17:24>[ARG1 x3]\n'
        '}'
    )

    assert eds.dumps_one(nearly_every_dog_barked, show_status=True) == (
        '{e2: (fragmented)\n'
        '|e5:_nearly_x_deg<0:6>[]\n'
        ' _1:_every_q<7:12>[BV x3]\n'
        ' x3:_dog_n_1<13:16>[]\n'
        ' e2:_bark_v_1<17:24>[ARG1 x3]\n'
        '}'
    )

    assert eds.dumps_one(nearly_every_dog_barked, predicate_modifiers=True) == (
        '{e2:\n'
        ' e5:_nearly_x_deg<0:6>[ARG1 _1]\n'
        ' _1:_every_q<7:12>[BV x3]\n'
        ' x3:_dog_n_1<13:16>[]\n'
        ' e2:_bark_v_1<17:24>[ARG1 x3]\n'
        '}'
    )

    assert eds.dumps_one(nearly_every_dog_barked,
                         predicate_modifiers=eds.non_argument_modifiers(role='MOD')) == (
        '{e2:\n'
        ' e5:_nearly_x_deg<0:6>[MOD _1]\n'
        ' _1:_every_q<7:12>[BV x3]\n'
        ' x3:_dog_n_1<13:16>[]\n'
        ' e2:_bark_v_1<17:24>[ARG1 x3]\n'
        '}'
    )

    assert eds.dumps_one(kim_probably_sleeps) == (
        '{e9:\n'
        ' _1:proper_q<0:3>[BV x3]\n'
        ' x3:named<0:3>("Kim")[]\n'
        ' e9:_probable_a_1<4:12>[ARG1 e2]\n'
        ' e2:_sleep_v_1<13:20>[ARG1 x3]\n'
        '}'
    )

def test_serialize_list():
    assert eds.dumps([it_rains, it_rains]) == (
        '{e2:\n'
        ' e2:_rain_v_1<3:9>[]\n'
        '}\n'
        '{e2:\n'
        ' e2:_rain_v_1<3:9>[]\n'
        '}'
    )

    assert eds.dumps([it_rains, it_rains], pretty_print=False) == (
        '{e2: e2:_rain_v_1<3:9>[]} {e2: e2:_rain_v_1<3:9>[]}'
    )
