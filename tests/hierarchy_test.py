
import pytest

from delphin.hierarchy import (
    MultiHierarchy as MH,
    HierarchyError)


@pytest.fixture
def h1():
    return MH('*top*', {'a': '*top*',
                        'b': ('*top*',),
                        'c': 'a b',
                        'd': ('a', 'b')})


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
        assert 'a' in h
        assert 'A' not in h  # case sensitive

        h = MH('*top*', {'a': '*top*', 'b': '*top*', 'c': 'a b'},
               normalize_identifier=str.upper)
        assert h.top == '*TOP*'
        assert sorted(h) == ['A', 'B', 'C']
        assert 'A' in h
        assert 'a' in h  # case normalized

    def test__eq__(self, h1):
        assert h1 == MH(h1.top, {id: h1.parents(id) for id in h1})
        assert h1 != MH(h1.top.upper(), {
            id.upper(): [p.upper() for p in h1.parents(id)]
            for id in h1})

    def test_parents(self, h1):
        assert h1.parents('d') == ('a', 'b')
        assert h1.parents('c') == ('a', 'b')
        assert h1.parents('b') == ('*top*',)
        assert h1.parents('a') == ('*top*',)
        assert h1.parents('*top*') == ()
        with pytest.raises(KeyError):
            h1.parents('e')

    def test_children(self, h1):
        assert h1.children('d') == set()
        assert h1.children('c') == set()
        assert h1.children('b') == {'c', 'd'}
        assert h1.children('a') == {'c', 'd'}
        assert h1.children('*top*') == {'a', 'b'}
        with pytest.raises(KeyError):
            h1.children('e')

    def test_ancestors(self, h1):
        assert h1.ancestors('d') == {'b', 'a', '*top*'}
        assert h1.ancestors('c') == {'b', 'a', '*top*'}
        assert h1.ancestors('b') == {'*top*'}
        assert h1.ancestors('a') == {'*top*'}
        assert h1.ancestors('*top*') == set()
        with pytest.raises(KeyError):
            h1.ancestors('e')

    def test_descendants(self, h1):
        assert h1.descendants('d') == set()
        assert h1.descendants('c') == set()
        assert h1.descendants('b') == {'c', 'd'}
        assert h1.descendants('a') == {'c', 'd'}
        assert h1.descendants('*top*') == {'a', 'b', 'c', 'd'}
        with pytest.raises(KeyError):
            h1.descendants('e')

    def test_update(self):
        h = MH('*top*')
        # single parent as string
        h.update({'a': '*top*', 'b': '*top*'})
        assert h.parents('a') == ('*top*',)
        # multiple parents as string
        h.update({'c': 'a b'})
        assert h.parents('c') == ('a', 'b')
        # parents as tuple
        h.update({'d': ('a',)})
        assert h.parents('d') == ('a',)
        # id already exists
        with pytest.raises(HierarchyError):
            h.update({'a': '*top*'})
        # parents don't exist
        with pytest.raises(HierarchyError):
            h.update({'a': 'f'})
        # updating data
        h.update(data={'d': 5})
        assert h['d'] == 5
        # failed update doesn't change hierarchy or data
        with pytest.raises(HierarchyError):
            h.update({'e': 'd'}, data={'a': 7, 'f': 9})
        assert 'e' not in 'h'
        assert h['a'] is None

    def test_get_set(self, h1):
        assert h1['a'] is None
        h1['a'] = 1
        h1.update(data={'b': 5, 'c': 6})
        assert h1['a'] == 1
        assert h1['b'] == 5
        assert h1['c'] == 6
        with pytest.raises(HierarchyError):
            h1['e'] = 7

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

    def test_subsumes(self):
        th = MH('*top*')
        assert th.subsumes('*top*', '*top*') is True
        th = MH('*top*', {'a': ['*top*']})
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
        th = MH('*top*')
        assert th.compatible('*top*', '*top*') is True
        th = MH('*top*', {'a': ['*top*']})
        assert th.compatible('*top*', 'a') is True
        th.update({'b': '*top*'})
        assert th.compatible('a', 'b') is False
        th.update({'c': 'a b'})
        assert th.compatible('a', 'b') is True

    def test_integrity(self):
        # trivial cycle
        with pytest.raises(HierarchyError):
            MH('*top*', {'a': ['*top*', 'a']})
        # mutual cycle
        with pytest.raises(HierarchyError):
            MH('*top*', {'a': ['*top*', 'b'], 'b': ['*top*', 'a']})
        # redundant parent
        with pytest.raises(HierarchyError):
            MH('*top*', {'a': ['*top*'], 'b': ['*top*', 'a']})
