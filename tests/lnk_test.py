
import pytest

from delphin.lnk import Lnk, LnkMixin, LnkError


class TestLnk():
    def test_raw_init(self):
        with pytest.raises(TypeError):
            Lnk()
        # don't allow just any Lnk type
        with pytest.raises(LnkError):
            Lnk('lnktype', (0, 1))

    def test__eq__(self):
        assert Lnk(None) == Lnk(None)
        assert Lnk(None) != Lnk.charspan(0, 1)
        assert Lnk.charspan(0, 1) == Lnk.charspan(0, 1)
        assert Lnk.charspan(0, 1) != Lnk.charspan(0, 2)
        assert Lnk.charspan(0, 1) != Lnk.chartspan(0, 1)

    def test__bool__(self):
        assert not Lnk(None)
        assert not Lnk.charspan(-1, -1)
        assert Lnk.charspan(0, 0)
        assert Lnk.chartspan(0, 0)
        assert Lnk.tokens([])
        assert Lnk.edge(0)

    def testDefault(self):
        lnk = Lnk.default()
        assert lnk.type == Lnk.UNSPECIFIED
        assert str(lnk) == ''
        repr(lnk)  # no error

    def testCharSpanLnk(self):
        lnk = Lnk.charspan(0, 1)
        assert lnk.type == Lnk.CHARSPAN
        assert lnk.data == (0, 1)
        assert str(lnk) == '<0:1>'
        repr(lnk)  # no error
        lnk = Lnk.charspan('0', '1')
        assert lnk.data == (0, 1)
        with pytest.raises(TypeError):
            Lnk.charspan(1)
        with pytest.raises(TypeError):
            Lnk.charspan([1, 2])
        with pytest.raises(TypeError):
            Lnk.charspan(1, 2, 3)
        with pytest.raises(ValueError):
            Lnk.charspan('a', 'b')

    def testChartSpanLnk(self):
        lnk = Lnk.chartspan(0, 1)
        assert lnk.type == Lnk.CHARTSPAN
        assert lnk.data == (0, 1)
        assert str(lnk) == '<0#1>'
        repr(lnk)  # no error
        lnk = Lnk.chartspan('0', '1')
        assert lnk.data == (0, 1)
        with pytest.raises(TypeError):
            Lnk.chartspan(1)
        with pytest.raises(TypeError):
            Lnk.chartspan([1, 2])
        with pytest.raises(TypeError):
            Lnk.chartspan(1, 2, 3)
        with pytest.raises(ValueError):
            Lnk.chartspan('a', 'b')

    def testTokensLnk(self):
        lnk = Lnk.tokens([1, 2, 3])
        assert lnk.type == Lnk.TOKENS
        assert lnk.data == (1, 2, 3)
        assert str(lnk) == '<1 2 3>'
        repr(lnk)  # no error
        lnk = Lnk.tokens(['1'])
        assert lnk.data == (1,)
        # empty tokens list might be invalid, but accept for now
        lnk = Lnk.tokens([])
        assert lnk.data == tuple()
        with pytest.raises(TypeError):
            Lnk.tokens(1)
        with pytest.raises(ValueError):
            Lnk.tokens(['a', 'b'])

    def testEdgeLnk(self):
        lnk = Lnk.edge(1)
        assert lnk.type == Lnk.EDGE
        assert lnk.data == 1
        assert str(lnk) == '<@1>'
        repr(lnk)  # no error
        lnk = Lnk.edge('1')
        assert lnk.data == 1
        with pytest.raises(TypeError):
            Lnk.edge(None)
        with pytest.raises(TypeError):
            Lnk.edge((1,))
        with pytest.raises(ValueError):
            Lnk.edge('a')


class TestLnkMixin():
    def test_inherit(self):
        class NoLnk(LnkMixin):
            pass
        n = NoLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithNoneLnk(LnkMixin):
            def __init__(self):
                self.lnk = None
        n = WithNoneLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithNonCharspanLnk(LnkMixin):
            def __init__(self):
                self.lnk = Lnk.chartspan(0, 1)
        n = WithNonCharspanLnk()
        assert n.cfrom == -1
        assert n.cto == -1

        class WithCharspanLnk(LnkMixin):
            def __init__(self):
                self.lnk = Lnk.charspan(0, 1)
        n = WithCharspanLnk()
        assert n.cfrom == 0
