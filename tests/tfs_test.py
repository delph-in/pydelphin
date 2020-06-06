
import pytest

from delphin import tfs


@pytest.fixture
def empty_fs():
    return tfs.FeatureStructure()


@pytest.fixture
def flat_fs():
    return tfs.FeatureStructure({'A': 'xYz', 'B': 2})


@pytest.fixture
def nested_fs():
    return tfs.FeatureStructure([('A.B.C', 1), ('A.B.D', 2), ('B', 3)])


class TestFeatureStructure():
    def test_init(self):
        tfs.FeatureStructure()
        tfs.FeatureStructure({'A': 'b'})
        tfs.FeatureStructure([('A', 'b')])
        tfs.FeatureStructure([('A.B.C', 1), ('A.B.D', 2), ('B', 3)])

    def test_eq(self, empty_fs, flat_fs, nested_fs):
        assert empty_fs == tfs.FeatureStructure()
        assert empty_fs != flat_fs
        assert flat_fs == flat_fs
        flat2 = tfs.FeatureStructure({'A': 'XyZ', 'B': 2})
        assert flat_fs != flat2
        flat3 = tfs.FeatureStructure({'a': 'xYz', 'b': 2})
        assert flat_fs == flat3
        flat4 = tfs.FeatureStructure({'A': 'xYz', 'B': 2, 'C': 1})
        assert flat_fs != flat4
        assert nested_fs == tfs.FeatureStructure([
            ('A', tfs.FeatureStructure({'B.C': 1, 'B.D': 2})),
            ('B', 3)])

    def test__setitem__(self, empty_fs):
        empty_fs['A'] = 1
        assert empty_fs['A'] == 1
        empty_fs['a'] = 3
        assert empty_fs['A'] == 3
        empty_fs['B.C'] = 4
        assert empty_fs['B'] == tfs.FeatureStructure({'C': 4})

    def test__setitem__issue293(self):
        t = tfs.FeatureStructure()
        t['A.B'] = 'c'
        with pytest.raises(tfs.TFSError):
            t['A.B.C'] = 'd'

    def test__getitem__(self, empty_fs, flat_fs, nested_fs):
        with pytest.raises(KeyError):
            empty_fs['unknown']
        assert flat_fs['A'] == 'xYz'  # case sensitive values
        assert flat_fs['A'] == flat_fs['a']  # case insensitive keys
        assert flat_fs['B'] == 2
        assert nested_fs['A.B.C'] == nested_fs['a.B.c'] == 1
        # dot notation vs nested feature structures
        assert nested_fs['A.B.D'] == nested_fs['A']['B']['D'] == 2
        with pytest.raises(KeyError):
            nested_fs['A.B.E']

    def test__delitem__(self, nested_fs):
        del nested_fs['A.B.C']
        assert 'A.B.C' not in nested_fs
        assert nested_fs['A.B.D'] == 2
        del nested_fs['A.B.D']
        assert nested_fs['A.B'] == tfs.FeatureStructure()
        del nested_fs['A']
        assert 'A' not in nested_fs
        del nested_fs['b']
        assert 'B' not in nested_fs

    def test__contains__(self):
        pass

    def test_get(self, empty_fs, flat_fs, nested_fs):
        assert empty_fs.get('unknown') is None
        assert flat_fs.get('A') == 'xYz'
        assert flat_fs.get('a') == flat_fs.get('A')  # case insensitive keys
        assert flat_fs.get('B') == 2

    def test_features(self, empty_fs, flat_fs, nested_fs):
        assert empty_fs.features() == []
        assert sorted(flat_fs.features()) == [('A', 'xYz'), ('B', 2)]
        assert sorted(nested_fs.features()) == [
            ('A.B', tfs.FeatureStructure([('C', 1), ('D', 2)])),
            ('B', 3)]
        assert sorted(nested_fs.features(expand=True)) == [
            ('A.B.C', 1), ('A.B.D', 2), ('B', 3)]


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
    def test_update(self):
        th = tfs.TypeHierarchy('*top*')
        # invalid parent data type
        with pytest.raises(TypeError):
            th.update({'1': 1})

    def test_integrity(self):
        pass
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
