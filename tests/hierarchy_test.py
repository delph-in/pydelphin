
import pytest

from delphin.hierarchy import (
    MultiHierarchy as MH,
    HierarchyError)


class TestMultiHierarchy():
    def test_init(self):
        with pytest.raises(TypeError):
            MH()
        with pytest.raises(HierarchyError):
            MH('*top*', {'a': 'b'})
        h = MH('*top*')
        assert h is not None
        h = MH('*top*', {'a': '*top*'}, {'a': 5})
        assert h.top == '*top*'
        h = MH('*top*', normalize_identifier=str.upper)
        assert h.top == '*TOP*'

    def test_parents(self):
        h = MH('*top*',
               {'a': '*top*', 'b': ('*top*',), 'c': 'a b', 'd': ('a', 'b')})
        assert h.parents('d') == ('a', 'b')
        assert h.parents('c') == ('a', 'b')
        assert h.parents('b') == ('*top*',)
        assert h.parents('a') == ('*top*',)
        assert h.parents('*top*') == ()
        with pytest.raises(KeyError):
            h.parents('e')

    def test_children(self):
        h = MH('*top*',
               {'a': '*top*', 'b': ('*top*',), 'c': 'a b', 'd': ('a', 'b')})
        assert h.children('d') == set()
        assert h.children('c') == set()
        assert h.children('b') == {'c', 'd'}
        assert h.children('a') == {'c', 'd'}
        assert h.children('*top*') == {'a', 'b'}
        with pytest.raises(KeyError):
            h.children('e')

    def test_ancestors(self):
        h = MH('*top*',
               {'a': '*top*', 'b': ('*top*',), 'c': 'a b', 'd': ('a', 'b')})
        assert h.ancestors('d') == {'b', 'a', '*top*'}
        assert h.ancestors('c') == {'b', 'a', '*top*'}
        assert h.ancestors('b') == {'*top*'}
        assert h.ancestors('a') == {'*top*'}
        assert h.ancestors('*top*') == set()
        with pytest.raises(KeyError):
            h.ancestors('e')

    def test_descendants(self):
        h = MH('*top*',
               {'a': '*top*', 'b': ('*top*',), 'c': 'a b', 'd': ('a', 'b')})
        assert h.descendants('d') == set()
        assert h.descendants('c') == set()
        assert h.descendants('b') == {'c', 'd'}
        assert h.descendants('a') == {'c', 'd'}
        assert h.descendants('*top*') == {'a', 'b', 'c', 'd'}
        with pytest.raises(KeyError):
            h.descendants('e')

    def test_update(self):
        h = MH('*top*')
        h.update({'a': '*top*', 'b': '*top*'})
        assert h.parents('a') == ('*top*',)
        h.update({'d': 'a'})
        assert h.parents('d') == ('a',)
        # no multiple parents
        with pytest.raises(HierarchyError):
            h.update({'c': 'b c'})
        # exists
        with pytest.raises(HierarchyError):
            h.update({'a': '*top*'})
        # parent doesn't exist
        with pytest.raises(HierarchyError):
            h.update({'a': 'f'})
        # invalid parent data type (note: type checks currently disabled)
        # with pytest.raises(TypeError):
        #     h.update({'c': ('a', 'b')})
        # with pytest.raises(TypeError):
        #     h.update({'1': 1})

    def test_get_set(self):
        h = MH('*top*')
        h.update({'a': '*top*'})
        assert h.parents('a') == ('*top*',)
        with pytest.raises(KeyError):
            h['A']  # case sensitive
        assert h.children('*top*') == {'a'}
        h.update({'b': '*top*'})
        # no multiple parents
        with pytest.raises(HierarchyError):
            h.update({'c': 'b c'})
        # exists
        with pytest.raises(HierarchyError):
            h.update({'a': '*top*'})
        # parent doesn't exist
        with pytest.raises(HierarchyError):
            h.update({'e': 'f'})
        # invalid parent data type (note: type checks currently disabled)
        # with pytest.raises(TypeError):
        #     h.update({'c': ('b', 'c')})
        # with pytest.raises(TypeError):
        #     h.update({'1': 1})

    def test_len(self):
        h = MH('*top*')
        assert len(h) == 0
        h.update({'a': '*top*'})
        assert len(h) == 1
        h.update({'b': '*top*'})
        h.update({'c': 'a'})
        assert len(h) == 3

    def test_iter(self):
        h = MH('*top*')
        assert list(h) == []
        h.update({'a': '*top*'})
        assert list(h) == ['a']

    def test_items(self):
        h = MH('*top*')
        assert h.items() == []
        h.update({'a': '*top*'})
        h.update({'b': '*top*'})
        assert len(h.items()) == 2
