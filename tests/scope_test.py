
from delphin import scope


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
