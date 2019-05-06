
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
    def test_update(self):
        th = tfs.TypeHierarchy('*top*')
        # invalid parent data type
        with pytest.raises(TypeError):
            th.update({'1': 1})

    def test_integrity(self):
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
