
import pytest

from delphin import hierarchy
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


class TestTypeHierarchy(object):
    def test_init(self):
        with pytest.raises(TypeError):
            tfs.TypeHierarchy()
        with pytest.raises(hierarchy.HierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['b']})
        th = tfs.TypeHierarchy('*top*')
        assert th is not None

    def test_get_set(self):
        th = tfs.TypeHierarchy('*top*', {'a': '*top*'})
        assert th.parents('a') == ('*top*',)
        assert th.parents('A') == ('*top*',)  # case insensitive
        assert th.children('*top*') == {'a'}
        th.update({'b': '*top*', 'c': 'a b'})
        assert th.parents('c') == ('a', 'b')
        # exists
        with pytest.raises(hierarchy.HierarchyError):
            th.update({'a': '*top*'})
        # parent doesn't exist
        with pytest.raises(hierarchy.HierarchyError):
            th.update({'e': 'f'})
        # invalid parent data type
        with pytest.raises(TypeError):
            th.update({'1': 1})

    def test_update(self):
        th = tfs.TypeHierarchy('*top*')
        th.update({'a': '*top*', 'b': '*top*'})
        assert th.parents('a') == ('*top*',)
        th.update({'c': ('a', 'b')})
        assert th.parents('c') == ('a', 'b')
        th.update({'d': 'a b'})
        assert th.parents('d') == ('a', 'b')
        # exists
        with pytest.raises(hierarchy.HierarchyError):
            th.update({'a': '*top*'})
        # parent doesn't exist
        with pytest.raises(hierarchy.HierarchyError):
            th.update({'a': 'f'})
        # invalid parent data type
        with pytest.raises(TypeError):
            th.update({'1': 1})
        # cycle
        with pytest.raises(hierarchy.HierarchyError):
            th.update({'e': ('a', 'f'), 'f': ('a', 'e')})

    def test_subsumes(self):
        th = tfs.TypeHierarchy('*top*')
        assert th.subsumes('*top*', '*top*') is True
        th = tfs.TypeHierarchy('*top*', {'a': ['*top*']})
        assert th.subsumes('*top*', 'a') is True
        assert th.subsumes('a', '*top*') is False
        th.update({'b': '*top*'})
        assert th.subsumes('a', 'b') is False
        assert th.subsumes('b', 'a') is False
        th.update({'c': ['a', 'b']})
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
        th.update({'b': '*top*'})
        assert th.compatible('a', 'b') is False
        th.update({'c': 'a b'})
        assert th.compatible('a', 'b') is True

    def test_len(self):
        th = tfs.TypeHierarchy('*top*')
        assert len(th) == 0
        th.update({'a': '*top*'})
        assert len(th) == 1
        th.update({'b': '*top*'})
        th.update({'c': ('a', 'b')})
        assert len(th) == 3

    def test_iter(self):
        th = tfs.TypeHierarchy('*top*')
        assert list(th) == []
        th.update({'a': '*top*'})
        assert list(th) == ['a']

    def test_items(self):
        th = tfs.TypeHierarchy('*top*')
        assert th.items() == []
        th.update({'a': '*top*'})
        th.update({'b': '*top*'})
        assert len(th.items()) == 2

    def test_integrity(self):
        # trivial cycle
        with pytest.raises(hierarchy.HierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['*top*', 'a']})
        # mutual cycle
        with pytest.raises(hierarchy.HierarchyError):
            tfs.TypeHierarchy('*top*', {'a': ['*top*', 'b'],
                                        'b': ['*top*', 'a']})
        # redundant parent
        with pytest.raises(hierarchy.HierarchyError):
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
