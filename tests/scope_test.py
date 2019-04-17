
import pytest

from delphin import scope


class TestScopeTree(object):

    def test_init(self):
        with pytest.raises(TypeError):
            scope.ScopeTree()
        with pytest.raises(TypeError):
            scope.ScopeTree('h0')

        st = scope.ScopeTree('h0', ['h1'])
        assert st.top == 'h0'
        assert st.tree == {'h1': set()}
        assert st.qeqs == {}

        st = scope.ScopeTree(
            'h0', ['h1', 'h2'], heqs=[('h1', 'h2')], qeqs=[('h0', 'h1')])
        assert st.top == 'h0'
        assert st.tree == {'h1': set(['h2']), 'h2': set()}
        assert st.qeqs == {'h0': set(['h1'])}

    def test_descendants(self):
        st = scope.ScopeTree('h0', ['h1'])
        assert st.descendants('h0') == set()
        assert st.descendants('h1') == set()

        st = scope.ScopeTree('h0', ['h1'], qeqs=[('h0', 'h1')])
        assert st.descendants('h0') == set(['h1'])
        assert st.descendants('h1') == set()

        st = scope.ScopeTree(
            'h0', ['h1', 'h2', 'h3'], heqs=[('h2', 'h3')], qeqs=[('h0', 'h1')])
        assert st.descendants('h0') == set(['h1'])
        assert st.descendants('h1') == set()
        assert st.descendants('h2') == set(['h3'])
        assert st.descendants('h3') == set()

        st = scope.ScopeTree(
            'h0', ['h1', 'h2', 'h3'],
            heqs=[('h1', 'h2'), ('h2', 'h3')],
            qeqs=[('h0', 'h1')])
        assert st.descendants('h0') == set(['h1', 'h2', 'h3'])
        assert st.descendants('h1') == set(['h2', 'h3'])
        assert st.descendants('h2') == set(['h3'])
        assert st.descendants('h3') == set()

        st = scope.ScopeTree(
            'h0', ['h1', 'h2'],
            heqs=[('h1', 'h2')],
            qeqs=[('h0', 'h1'), ('h2', 'h1')])
        with pytest.raises(scope.ScopeError):
            st.descendants('h0')

    def test_outscopes(self):
        st = scope.ScopeTree(
            'h0', ['h1', 'h2', 'h3'], heqs=[('h2', 'h3')], qeqs=[('h0', 'h1')])
        assert st.outscopes('h0', 'h1')
        assert not st.outscopes('h1', 'h0')
        assert not st.outscopes('h0', 'h2')
        assert not st.outscopes('h0', 'h3')
        assert not st.outscopes('h1', 'h2')
        assert st.outscopes('h2', 'h3')
        assert not st.outscopes('h3', 'h0')

        st = scope.ScopeTree(
            'h0', ['h1', 'h2', 'h3'],
            heqs=[('h1', 'h2'), ('h2', 'h3')],
            qeqs=[('h0', 'h1')])
        assert st.outscopes('h0', 'h1')
        assert not st.outscopes('h1', 'h0')
        assert st.outscopes('h0', 'h2')
        assert st.outscopes('h0', 'h3')
        assert st.outscopes('h1', 'h2')
        assert st.outscopes('h2', 'h3')
        assert not st.outscopes('h3', 'h0')

def test_conjoin():
    assert scope.conjoin(['h0', 'h1'], []) == {'h0': {'h0'}, 'h1': {'h1'}}
    conj = scope.conjoin(['h0', 'h1'], [('h0', 'h1')])
    assert len(conj) == 1 and list(conj.values()) == [{'h0', 'h1'}]
    conj = scope.conjoin(['h0', 'h1', 'h2', 'h3'],
                         [('h0', 'h1'), ('h2', 'h3')])
    assert len(conj) == 2
    assert {'h0', 'h1'} in conj.values()
    assert {'h2', 'h3'} in conj.values()
    conj = scope.conjoin(['h0', 'h1', 'h2', 'h3'],
                         [('h0', 'h1'), ('h1', 'h2'), ('h2', 'h3')])
    assert len(conj) == 1
    assert {'h0', 'h1', 'h2', 'h3'} in conj.values()
