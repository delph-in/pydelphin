
from delphin import scope


class TestUnderspecifiedScope(object):
    def test_init(self):
        us = scope.UnderspecifiedScope([], [], [])
        assert tuple(us) == (set(), {}, {})
        us = scope.UnderspecifiedScope(
            ['e2'], {}, {'h1': scope.UnderspecifiedScope(['x4'])})
        assert tuple(us) == (
            {'e2'}, {}, {'h1': scope.UnderspecifiedScope(['x4'], {}, {})})
        assert us.ids == set(['e2'])
        assert us.lheqs == {}
        assert us.qeqs == {'h1': scope.UnderspecifiedScope(['x4'], {}, {})}

    def test__repr__(self):
        # just test for errors
        repr(scope.UnderspecifiedScope(['x4'], {}, {}))
        repr(scope.UnderspecifiedScope(
            ['x4'], {}, {'h5': scope.UnderspecifiedScope('x6')}))

    def test__contains__(self):
        us = scope.UnderspecifiedScope([], [], [])
        assert 'x5' not in us
        us = scope.UnderspecifiedScope(
            ['e2'], {}, {'h1': scope.UnderspecifiedScope(['x4'])})
        assert 'e2' in us
        assert 'x4' in us
        assert 'h1' not in us


def test_conjoin():
    assert scope.conjoin(
        {'h0': [], 'h1': ['e2']}, []) == {'h0': [], 'h1': ['e2']}
    conj = scope.conjoin({'h0': [], 'h1': ['e2']}, [('h0', 'h1')])
    assert len(conj) == 1 and list(conj.values()) == [['e2']]
    conj = scope.conjoin({'h0': [], 'h1': ['e2'], 'h2': ['x4'], 'h3': ['q5']},
                         [('h0', 'h1'), ('h2', 'h3')])
    assert len(conj) == 2
    vals = list(map(set, conj.values()))
    assert {'e2'} in vals
    assert {'x4', 'q5'} in vals
    conj = scope.conjoin({'h0': [], 'h1': ['e2'], 'h2': ['x4'], 'h3': ['q5']},
                         [('h0', 'h1'), ('h1', 'h2'), ('h2', 'h3')])
    assert len(conj) == 1
    assert {'e2', 'x4', 'q5'} == set(next(iter(conj.values())))


def test_tree_fragments():
    pass


def test_representatives():
    pass
