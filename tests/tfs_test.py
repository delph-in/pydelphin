
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

    fs = tfs.FeatureStructure([('A.B', 1), ('A.C', 2), ('B', 3)])
    assert sorted(fs.features()) == [
        ('A', tfs.FeatureStructure([('B', 1), ('C', 2)])),
        ('B', 3)]
    assert fs['A.B'] == fs['a.B'] == 1
    assert fs['A.C'] == fs['A']['C'] == 2
    assert fs['B'] == 3
    assert fs['A'] == tfs.FeatureStructure([('B', 1), ('C', 2)])
    with pytest.raises(KeyError):
        fs['A.D']

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
