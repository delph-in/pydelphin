
import pytest

from delphin.tokens import YYTokenLattice as YY, YYToken
from delphin.lnk import Lnk

token_v1_basic = '(1, 0, 1, 1, "dog", 0, "null")'
token_v1_surface = '(1, 0, 1, 1, "dog" "Dog", 0, "null")'
token_v1_pos = '(1, 0, 1, 1, "dog", 0, "null", "NN" 0.8 "VV" 0.2000)'
token_v1_surface_pos = '(1, 0, 1, 1, "dog" "Dog", 0, "null", "NN" 1.0000)'
token_v1_lrules = '(1, 0, 1, 1, "dog", 0, "lrule1" "lrule2")'
token_v2 = '(1, 0, 1, <1:3>, 1, "dog" "Dog", 0, "null", "NN" 1.0000)'

tokenstring = (
  '(42, 0, 1, <0:12>, 1, "Tokenization", 0, "null", "NNP" 0.7677 "NN" 0.2323) '
  '(43, 1, 2, <12:13>, 1, ",", 0, "null", "," 1.0000) '
  '(44, 2, 3, <14:15>, 1, "a", 0, "null", "DT" 1.0000) '
  '(45, 3, 4, <16:27>, 1, "non-trivial", 0, "null", "JJ" 1.0000) '
  '(46, 4, 5, <28:36>, 1, "exercise", 0, "null", "NN" 0.9887 "VB" 0.0113) '
  '(47, 5, 6, <36:37>, 1, ",", 0, "null", "," 1.0000) '
  '(48, 6, 7, <38:44>, 1, "bazed", 0, "null", "VBD" 0.5975 "VBN" 0.4025) '
  '(49, 7, 8, <45:58>, 1, "oe@ifi.uio.no", 0, "null", "NN" 0.7342 "JJ" 0.2096) '
  '(50, 8, 9, <58:59>, 1, ".", 0, "null", "." 1.0000)'
)


def check_token(t, id, start, end, lnk, paths, form, surf, ipos, lrules, pos):
    assert t.id == id
    assert t.start == start
    assert t.end == end
    if lnk:
        assert t.lnk == lnk
    else:
        assert not t.lnk
    assert t.paths == paths
    assert t.form == form
    assert t.surface == surf
    assert t.ipos == ipos
    assert t.lrules == lrules
    assert t.pos == pos


class TestYYToken(object):
    def test_init(self):
        with pytest.raises(TypeError):
            YYToken()
            YYToken(1)
            YYToken(1, 0)
            YYToken(1, 0, 1)
            YYToken(1, 0, 1, Lnk.charspan(0, 1))
            YYToken(1, 0, 1, Lnk.charspan(0, 1), [1])
            YYToken(1, 0, 1, Lnk.charspan(0, 1), [1], surface=".")
            YYToken(1, 0, 1, Lnk.charspan(0, 1), [1], surface=".", ipos=0)
            YYToken(1, 0, 1, Lnk.charspan(0, 1), [1], surface=".",
                    ipos=0, lrules=["null"])
            YYToken(1, 0, 1, Lnk.charspan(0, 1), [1], surface=".",
                    ipos=0, lrules=["null"], pos=[(".", 1.0)])
        t = YYToken(1, 0, 1, form="dog")
        check_token(t, 1, 0, 1, None, [1], "dog", None, 0, ["null"], [])
        t = YYToken(1, 0, 1, Lnk.charspan(0, 1), [1], "dog", "Dog",
                    ipos=0, lrules=["null"], pos=[("NN", 1.0)])
        check_token(t, 1, 0, 1, Lnk.charspan(0, 1), [1], "dog", "Dog",
                    0, ["null"], [("NN", 1.0)])

    def test_from_dict(self):
        t = YYToken.from_dict({'id': 1, 'start': 0, 'end': 1, 'form': "dog"})
        check_token(t, 1, 0, 1, None, [1], "dog", None, 0, ["null"], [])
        t = YYToken.from_dict({
            'id': 1, 'start': 0, 'end': 1, 'from': 0, 'to': 1,
            # 'paths': [1],
            'form': "dog", 'surface': "Dog",
            # 'ipos': 0, 'lrules': ["null"],
            'tags': ["NN"], 'probabilities': [1.0]
        })
        check_token(t, 1, 0, 1, Lnk.charspan(0, 1), [1], "dog", "Dog",
                    0, ["null"], [("NN", 1.0)])

    def test_to_dict(self):
        t = YYToken(1, 0, 1, form="dog")
        assert t.to_dict() == {'id': 1, 'start': 0, 'end': 1, 'form': "dog"}
        t = YYToken(1, 0, 1, Lnk.charspan(0, 1), [1], "dog", "Dog",
                    ipos=0, lrules=["null"], pos=[("NN", 1.0)])
        assert t.to_dict() == {
            'id': 1, 'start': 0, 'end': 1, 'from': 0, 'to': 1,
            # 'paths': [1],
            'form': "dog", 'surface': "Dog",
            # 'ipos': 0, 'lrules': ["null"],
            'tags': ["NN"], 'probabilities': [1.0]
        }


class TestYYTokenLattice(object):

    def test_fromstring(self):
        assert len(YY.from_string(token_v1_basic).tokens) == 1
        t = YY.from_string(token_v1_basic).tokens[0]
        check_token(t, 1, 0, 1, None, [1], "dog", None, 0, ["null"], [])
        t = YY.from_string(token_v1_surface).tokens[0]
        check_token(t, 1, 0, 1, None, [1], "dog", "Dog", 0, ["null"], [])
        t = YY.from_string(token_v1_pos).tokens[0]
        check_token(t, 1, 0, 1, None, [1], "dog", None, 0, ["null"],
                    [("NN", 0.8), ("VV", 0.2)])
        t = YY.from_string(token_v1_surface_pos).tokens[0]
        check_token(t, 1, 0, 1, None, [1], "dog", "Dog", 0, ["null"],
                    [("NN", 1.0)])
        t = YY.from_string(token_v1_lrules).tokens[0]
        check_token(t, 1, 0, 1, None, [1], "dog", None, 0,
                    ["lrule1", "lrule2"], [])
        t = YY.from_string(token_v2).tokens[0]
        check_token(t, 1, 0, 1, Lnk.charspan(1, 3), [1], "dog", "Dog",
                    0, ["null"], [("NN", 1.0)])
        tl = YY.from_string(tokenstring)
        assert len(tl.tokens) == 9
        check_token(
            tl.tokens[0],
            42, 0, 1, Lnk.charspan(0, 12), [1], "Tokenization", None,
            0, ["null"], [("NNP", 0.7677), ("NN", 0.2323)]
        )
        check_token(
            tl.tokens[1],
            43, 1, 2, Lnk.charspan(12, 13), [1], ",", None,
            0, ["null"], [(",", 1.0000)]
        )
        check_token(
            tl.tokens[2],
            44, 2, 3, Lnk.charspan(14, 15), [1], "a", None,
            0, ["null"], [("DT", 1.0000)]
        )
        check_token(
            tl.tokens[3],
            45, 3, 4, Lnk.charspan(16, 27), [1], "non-trivial", None,
            0, ["null"], [("JJ", 1.0000)]
        )
        check_token(
            tl.tokens[4],
            46, 4, 5, Lnk.charspan(28, 36), [1], "exercise", None,
            0, ["null"], [("NN", 0.9887), ("VB", 0.0113)]
        )
        check_token(
            tl.tokens[5],
            47, 5, 6, Lnk.charspan(36, 37), [1], ",", None,
            0, ["null"], [(",", 1.0000)]
        )
        check_token(
            tl.tokens[6],
            48, 6, 7, Lnk.charspan(38, 44), [1], "bazed", None,
            0, ["null"], [("VBD", 0.5975), ("VBN", 0.4025)]
        )
        check_token(
            tl.tokens[7],
            49, 7, 8, Lnk.charspan(45, 58), [1], "oe@ifi.uio.no", None,
            0, ["null"], [("NN", 0.7342), ("JJ", 0.2096)]
        )
        check_token(
            tl.tokens[8],
            50, 8, 9, Lnk.charspan(58, 59), [1], ".", None,
            0, ["null"], [(".", 1.0000)]
        )

    def test_from_list(self):
        tl = YY.from_list(
            [{'id': 1, 'start': 0, 'end': 1, 'form': "dog"}]
        )
        assert tl.tokens == [YYToken(1, 0, 1, form="dog")]

        tl = YY.from_list(
            [
                {'id': 1, 'start': 0, 'end': 1, 'from': 0, 'to': 4,
                 'paths': [1], 'form': "dogs", 'surface': "Dogs",
                 # 'ipos': 0, 'lrules': ["null"],
                 'tags': ["NN"], 'probabilities': [1.0]
                },
                {'id': 1, 'start': 0, 'end': 1, 'from': 5, 'to': 9,
                 'paths': [1], 'form': "bark",
                 # 'ipos': 0, 'lrules': ["null"],
                 'tags': ["VBZ"], 'probabilities': [1.0]
                }
            ]
        )
        assert tl.tokens == [
            YYToken(1, 0, 1, Lnk.charspan(0, 4), [1], "dogs", "Dogs",
                    ipos=0, lrules=["null"], pos=[("NN", 1.0)]),
            YYToken(1, 0, 1, Lnk.charspan(5, 9), [1], "bark",
                    ipos=0, lrules=["null"], pos=[("VBZ", 1.0)])
        ]

    def test_to_list(self):
        tl = YY([YYToken(1, 0, 1, form="dog")])
        assert tl.to_list() == [{'id': 1, 'start': 0, 'end': 1, 'form': "dog"}]

        tl = YY([
            YYToken(1, 0, 1, Lnk.charspan(0, 4), [1], "dogs", "Dogs",
                    ipos=0, lrules=["null"], pos=[("NN", 1.0)]),
            YYToken(2, 1, 2, Lnk.charspan(5, 9), [1], "bark",
                    ipos=0, lrules=["null"], pos=[("VBZ", 1.0)])
        ])
        assert tl.to_list() == [
            {'id': 1, 'start': 0, 'end': 1, 'from': 0, 'to': 4,
             'form': "dogs", 'surface': "Dogs",
             # 'ipos': 0, 'lrules': ["null"],
             'tags': ["NN"], 'probabilities': [1.0]
            },
            {'id': 2, 'start': 1, 'end': 2, 'from': 5, 'to': 9,
             'form': "bark",
             # 'ipos': 0, 'lrules': ["null"],
             'tags': ["VBZ"], 'probabilities': [1.0]
            }
        ]

    def test_str(self):
        assert str(YY.from_string(token_v1_basic).tokens[0]) == token_v1_basic
        assert str(YY.from_string(token_v2).tokens[0]) == token_v2
        assert str(YY.from_string(tokenstring)) == tokenstring
