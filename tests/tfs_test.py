
import pytest

from delphin import tfs


def test_FeatureStructure():
    fs = tfs.FeatureStructure()
    assert fs.features() == []
    with pytest.raises(KeyError):
        fs['unknown']
    assert fs.get('unknown') is None
    assert fs == tfs.FeatureStructure()

    fs = tfs.FeatureStructure({'A': 'xYz', 'B': 2})
    assert sorted(fs.features()) == [('A', 'xYz'), ('B', 2)]
    assert fs['A'] == fs.get('A') == 'xYz'  # case sensitive values
    assert fs['A'] == fs['a']  # case insensitive keys
    assert fs['B'] == fs.get('B') == 2
    assert fs == tfs.FeatureStructure([('A', 'xYz'), ('B', 2)])

    fs = tfs.FeatureStructure([('A.B.C', 1), ('A.B.D', 2), ('B', 3)])
    assert sorted(fs.features()) == [
        ('A.B', tfs.FeatureStructure([('C', 1), ('D', 2)])),
        ('B', 3)]
    assert sorted(fs.features(expand=True)) == [
        ('A.B.C', 1), ('A.B.D', 2), ('B', 3)]
    assert fs['A.B.C'] == fs['a.B.c'] == 1
    assert fs['A.B.D'] == fs['A']['B']['D'] == 2
    assert fs['B'] == 3
    assert fs['A'] == tfs.FeatureStructure([('B.C', 1), ('B.D', 2)])
    with pytest.raises(KeyError):
        fs['A.B.E']


def test_TypedFeatureStructure():
    with pytest.raises(TypeError):
        tfs.TypedFeatureStructure()

    fs = tfs.TypedFeatureStructure('typename')
    assert fs.type == 'typename'
    assert fs.features() == []

    fs = tfs.TypedFeatureStructure('typename', [('a', 1), ('b', 2)])
    assert fs.type == 'typename'
    assert fs.features() == [('A', 1), ('B', 2)]
    assert fs == tfs.TypedFeatureStructure('typename', [('A', 1), ('B', 2)])
    assert fs != tfs.TypedFeatureStructure('name', [('A', 1), ('B', 2)])
    assert fs != tfs.TypedFeatureStructure('typename', [('A', 1), ('B', 3)])


def test_TypeHierarchyNode():
    N = tfs.TypeHierarchyNode
    with pytest.raises(TypeError):
        N()
    with pytest.raises(ValueError):
        N([])
    n = N.top()
    assert n.parents == []
    n = N(['*top*'])
    assert n.parents == ['*top*']
    assert n.children == []
    assert n.data is None
    n.data = 1
    assert n.data == 1
    n = N(['a', 'b'], data=2)
    assert n.parents == ['a', 'b']
    assert n.data == 2
    # case normalization
    n = N(['A', 'b'])
    assert n.parents == ['a', 'b']


class TypeHierarchyTest():
    def test_init(self):
        with pytest.raises(TypeError):
            tfs.TypeHierarchy()
        with pytest.raises(tfs.TypeHierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['b']})
        th = tfs.TypeHierarchy('*top*')
        assert th is not None

    def test_get_set(self):
        th = tfs.TypeHierarchy('*top*')
        th['a'] = '*top*'
        assert th['a'].parents == ['*top*']
        assert th['A'].parents == ['*top*']  # case insensitive
        assert th['*top*'].children == ['a']
        th['b'] = '*top*'
        th['c'] = ('a', 'b')
        assert th['c'].parents == ['a', 'b']
        th['d'] = tfs.TypeHierarchyNode(['c'])
        assert th['d'].parents == ['c']
        # exists
        with pytest.raises(tfs.TypeHierarchyError):
            th['a'] = '*top*'
        # parent doesn't exist
        with pytest.raises(tfs.TypeHierarchyError):
            th['e'] = 'f'
        # invalid parent data type
        with pytest.raises(tfs.TypeHierarchyError):
            th['1'] = 1

    def test_update(self):
        th = tfs.TypeHierarchy('*top*')
        th.update({'a': '*top*', 'b': '*top*'})
        assert th['a'].parents == ['*top*']
        th.update({'c': ('a', 'b')})
        assert th['c'].parents == ['a', 'b']
        th.update({'d': tfs.TypeHierarchyNode(['a'])})
        assert th['d'].parents == 'a'
        # exists
        with pytest.raises(tfs.TypeHierarchyError):
            th.update({'a': '*top*'})
        # parent doesn't exist
        with pytest.raises(tfs.TypeHierarchyError):
            th.update({'a': '*top*'})
        # invalid parent data type
        with pytest.raises(tfs.TypeHierarchyError):
            th.update({'1': 1})
        # cycle
        with pytest.raises(tfs.TypeHierarchyError):
            th.update({'e': ('a', 'f'), 'f': ('a', 'e')})

    def test_subsumes(self):
        th = tfs.TypeHierarchy('*top*')
        assert th.subsumes('*top*', '*top*') is True
        th = tfs.TypeHierarchy('*top*', {'a': ['*top*']})
        assert th.subsumes('*top*', 'a') is True
        assert th.subsumes('a', '*top*') is False
        th['b'] = ['*top*']
        assert th.subsumes('a', 'b') is False
        assert th.subsumes('b', 'a') is False
        th['c'] = ['a', 'b']
        assert th.subsumes('a', 'b') is False
        assert th.subsumes('b', 'a') is False
        assert th.subsumes('a', 'c') is True
        assert th.subsumes('b', 'c') is True
        assert th.subsumes('*top*', 'c') is True
        assert th.subsumes('c', 'a') is False
        assert th.subsumes('c', 'b') is False

    def test_compatible(self):
        th = tfs.TypeHierarchy('*top*')
        assert th.compatible('*top*', '*top*') is True
        th = tfs.TypeHierarchy('*top*', {'a': ['*top*']})
        assert th.compatible('*top*', 'a') is True
        th['b'] = ['*top*']
        assert th.compatible('a', 'b') is False
        th['c'] = ['a', 'b']
        assert th.compatible('a', 'b') is True

    def test_len(self):
        th = tfs.TypeHierarchy('*top*')
        assert len(th) == 0
        th['a'] = '*top*'
        assert len(th) == 1
        th['b'] = '*top*'
        th['c'] = ('a', 'b')
        assert len(th) == 3

    def test_iter(self):
        th = tfs.TypeHierarchy('*top*')
        assert list(th) == []
        th['a'] = '*top*'
        assert list(th) == ['a']

    def test_items(self):
        th = tfs.TypeHierarchy('*top*')
        assert th.items() == []
        th['a'] = '*top*'
        th['b'] = '*top*'
        assert len(th.items()) == 2

    def test_integrity(self):
        # trivial cycle
        with pytest.raises(tfs.TypeHierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['*top*', 'a']})
        # mutual cycle
        with pytest.raises(tfs.TypeHierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['*top*', 'b'],
                                        'b': ['*top*', 'a']})
        # redundant parent
        with pytest.raises(tfs.TypeHierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['*top*'],
                                        'b': ['*top*', 'a']})
        # awaiting issue #94
        # # non-unique glb
        # with pytest.raises(tfs.TypeHierarchyError):
        #     tfs.TypeHierarchy('*top*', {'a': ['*top*'],
        #                                 'b': ['*top*'],
        #                                 'c': ['a', 'b'],
        #                                 'd': ['a', 'b']})
        # # non-symmetric non-unique glb
        # with pytest.raises(tfs.TypeHierarchyError):
        #     tfs.TypeHierarchy('*top*', {'a': ['*top*'],
        #                                 'b': ['*top*'],
        #                                 'c': ['*top*'],
        #                                 'd': ['a', 'b', 'c'],
        #                                 'e': ['a', 'b']})
        # # non-immediate non-unique glb
        # with pytest.raises(tfs.TypeHierarchyError):
        #     tfs.TypeHierarchy('*top*', {'a': ['*top*'],
        #                                 'b': ['*top*'],
        #                                 'c': ['a', 'b'],
        #                                 'a2': ['a'],
        #                                 'b2': ['b'],
        #                                 'd': ['a2', 'b2']})
