
import pytest

from delphin.hierarchy import (HierarchyNode, Hierarchy, HierarchyError)


def test_HierarchyNode():
    N = HierarchyNode
    with pytest.raises(TypeError):
        N()
    n = N(None)
    assert n.parent is None
    n = N('*top*')
    assert n.parent == '*top*'
    assert n.children == []
    assert n.data is None
    n.data = 1
    assert n.data == 1
    n = N(('a', 'b'), data=2)
    assert n.parent == ('a', 'b')
    assert n.data == 2
    # no case normalization
    n = N('A')
    assert n.parent == 'A'


class TestHierarchy():
    def test_init(self):
        with pytest.raises(TypeError):
            Hierarchy()
        with pytest.raises(HierarchyError):
            Hierarchy('*top*', {'a': 'b'})
        h = Hierarchy('*top*')
        assert h is not None

    def test_get_set(self):
        h = Hierarchy('*top*')
        h['a'] = '*top*'
        assert h['a'].parent == '*top*'
        with pytest.raises(KeyError):
            h['A']  # case sensitive
        assert h['*top*'].children == ['a']
        h['b'] = '*top*'
        # no multiple parents
        with pytest.raises(HierarchyError):
            h['c'] = HierarchyNode(('b', 'c'))
        # exists
        with pytest.raises(HierarchyError):
            h['a'] = '*top*'
        # parent doesn't exist
        with pytest.raises(HierarchyError):
            h['e'] = 'f'
        # invalid parent data type
        with pytest.raises(TypeError):
            h['c'] = ('b', 'c')
        with pytest.raises(TypeError):
            h['1'] = 1

    def test_update(self):
        h = Hierarchy('*top*')
        h.update({'a': '*top*', 'b': '*top*'})
        assert h['a'].parent == '*top*'
        h.update({'d': HierarchyNode('a')})
        assert h['d'].parent == 'a'
        # no multiple parents
        with pytest.raises(HierarchyError):
            h.update({'c': HierarchyNode(('b', 'c'))})
        # exists
        with pytest.raises(HierarchyError):
            h.update({'a': '*top*'})
        # parent doesn't exist
        with pytest.raises(HierarchyError):
            h.update({'a': 'f'})
        # invalid parent data type
        with pytest.raises(TypeError):
            h.update({'c': ('a', 'b')})
        with pytest.raises(TypeError):
            h.update({'1': 1})

    def test_len(self):
        h = Hierarchy('*top*')
        assert len(h) == 0
        h['a'] = '*top*'
        assert len(h) == 1
        h['b'] = '*top*'
        h['c'] = 'a'
        assert len(h) == 3

    def test_iter(self):
        h = Hierarchy('*top*')
        assert list(h) == []
        h['a'] = '*top*'
        assert list(h) == ['a']

    def test_items(self):
        h = Hierarchy('*top*')
        assert h.items() == []
        h['a'] = '*top*'
        h['b'] = '*top*'
        assert len(h.items()) == 2
