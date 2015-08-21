import pytest

from delphin.derivation import Derivation as D

class TestDerivation():
    def test_init(self):
        with pytest.raises(TypeError): D()
        with pytest.raises(TypeError): D(1)
        t = D(1, 'some-type')
        t = D(1, 'some-type', 0.5, 0, 3, [('some-token',)])
        # roots are special: id is None, entity is root, daughters must
        # exactly 1 node; rest are None
        with pytest.raises(TypeError): t = D(None)
        with pytest.raises(TypeError): t = D(None, 'some-root', 0.5)
        with pytest.raises(TypeError): t = D(None, 'some-root', start=1)
        with pytest.raises(TypeError): t = D(None, 'some-root', end=1)
        with pytest.raises(ValueError):
            t = D(None, 'some-root',
                   daughters=[D(1, 'some-type'), D(2, 'some-type')])
        with pytest.raises(ValueError):
            t = D(None, 'some-root', daughters=[('some-token',)])
        t = D(None, 'some-root', daughters=[D(1, 'some-type')])
        t = D(None, 'some-root', None, None, None,
               daughters=[D(1, 'some-type')])
        # root not as top
        with pytest.raises(ValueError):
            D(1, 'some-type', daughters=[
                D(None, 'some-root', daughters=[
                    D(2, 'a-lex', daughters=[('some-token',)])
                ])
            ])

    def test_attributes(self):
        t = D(1, 'some-type')
        assert t.id == 1
        assert t.entity == 'some-type'
        assert t.score == -1
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == []
        t = D(1, 'some-type', 0.5, 1, 6, ['some token'])
        assert t.id == 1
        assert t.entity == 'some-type'
        assert t.score == 0.5
        assert t.start == 1
        assert t.end == 6
        assert t.daughters == ['some token']
        t = D(None, 'some-root', daughters=[D(1, 'some-type')])
        assert t.id == None
        assert t.entity == 'some-root'
        assert t.score == None
        assert t.start == None
        assert t.end == None
        assert len(t.daughters) == 1

    def test_fromstring(self):
        with pytest.raises(ValueError): D.from_string('')
        # root with no children
        with pytest.raises(ValueError): D.from_string('(some-root)')
        # does not start with `(` or end with `)`
        with pytest.raises(ValueError):
            D.from_string(' (1 some-type -1 -1 -1 ("token"))')
        with pytest.raises(ValueError):
            D.from_string(' (1 some-type -1 -1 -1 ("token")) ')
        # uneven parens
        with pytest.raises(ValueError):
            D.from_string('(1 some-type -1 -1 -1 ("token")')
        # ok
        t = D.from_string('(1 some-type -1 -1 -1 ("token"))')
        assert t.id == 1
        assert t.entity == 'some-type'
        assert t.score == -1.0
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == [('"token"',)]
        # newlines in tree
        t = D.from_string('''(1 some-type -1 -1 -1
                                ("token"))''')
        assert t.id == 1
        assert t.entity == 'some-type'
        assert t.score == -1.0
        assert t.start == -1
        assert t.end == -1
        assert t.daughters == [('"token"',)]
        # longer example
        t = D.from_string(r'''(root
            (1 some-type 0.4 0 5
                (2 a-lex 0.8 0 1
                    ("a" 1 "token [ +FORM \"a\" ]"))
                (3 bcd-lex 0.5 2 5
                    ("bcd" 2 "token [ +FORM \"bcd\" ]")))
        )''')
        assert t.entity == 'root'
        assert len(t.daughters) == 1
        top = t.daughters[0]
        assert top.id == 1
        assert top.entity == 'some-type'
        assert top.score == 0.4
        assert top.start == 0
        assert top.end == 5
        assert len(top.daughters) == 2
        lex = top.daughters[0]
        assert lex.id == 2
        assert lex.entity == 'a-lex'
        assert lex.score == 0.8
        assert lex.start == 0
        assert lex.end == 1
        assert lex.daughters == [('"a"', '1', r'"token [ +FORM \"a\" ]"')]
        lex = top.daughters[1]
        assert lex.id == 3
        assert lex.entity == 'bcd-lex'
        assert lex.score == 0.5
        assert lex.start == 2
        assert lex.end == 5
        assert lex.daughters == [('"bcd"', '2', r'"token [ +FORM \"bcd\" ]"')]

    def test_str(self):
        s = '(1 some-type -1 -1 -1 ("token"))'
        assert str(D.from_string(s)) == s
        s = (r'(root (1 some-type 0.4 0 5 (2 a-lex 0.8 0 1 '
             r'("a" 1 "token [ +FORM \"a\" ]")) '
             r'(3 bcd-lex 0.5 2 5 ("bcd" 2 "token [ +FORM \"bcd\" ]"))))')
        assert str(D.from_string(s)) == s

    def test_eq(self):
        a = D.from_string('(1 some-type -1 -1 -1 ("token"))')
        # identity
        b = D.from_string('(1 some-type -1 -1 -1 ("token"))')
        assert a == b
        # ids and scores don't matter
        b = D.from_string('(100 some-type 0.114 -1 -1 ("token"))')
        assert a == b
        # tokens matter
        b = D.from_string('(1 some-type -1 -1 -1 ("nekot"))')
        assert a != b
        # and type of rhs
        assert a != '(1 some-type -1 -1 -1 ("token"))'
        # and tokenization
        b = D.from_string('(1 some-type -1 2 7 ("token"))')
        assert a != b
        # and of course entities
        b = D.from_string('(1 epyt-emos -1 -1 -1 ("token"))')
        assert a != b
        # and number of children
        a = D.from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")))')
        b = D.from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        assert a != b
        # and order of children
        a = D.from_string('(1 x -1 -1 -1 (2 y -1 -1 -1 ("y")) (3 z -1 -1 -1 ("z")))')
        b = D.from_string('(1 x -1 -1 -1 (3 z -1 -1 -1 ("z")) (2 y -1 -1 -1 ("y")))')
        assert a != b

    def test_is_root(self):
        a = D.from_string('(1 some-type -1 -1 -1 ("token"))')
        assert a.is_root() == False
        a = D.from_string('(root (1 some-type -1 -1 -1 ("token")))')
        assert a.is_root() == True
        assert a.daughters[0].is_root() == False

    def test_is_head(self):
        # NOTE: is_head() is undefined for standard UDF without the
        # head marker ^
        a = D.from_string('(root (1 some-type -1 -1 -1 ("a"))'
                          '      (2 ^some-type -1 -1 -1 ("b")))')
        assert a.daughters[0].is_head() == False
        assert a.daughters[1].is_head() == True

    def test_basic_entity(self):
        # this works for both UDX and standard UDF
        a = D.from_string('(root (1 a-type -1 -1 -1 ("a"))'
                          '      (2 b-type -1 -1 -1 ("b")))')
        assert a.basic_entity() == 'root'
        assert a.daughters[0].basic_entity() == 'a-type'
        assert a.daughters[1].basic_entity() == 'b-type'
        a = D.from_string('(root (1 a-type@a-type_le -1 -1 -1 ("a"))'
                          '      (2 b-type@b-type_le -1 -1 -1 ("b")))')
        assert a.basic_entity() == 'root'
        assert a.daughters[0].entity == 'a-type@a-type_le'
        assert a.daughters[0].basic_entity() == 'a-type'
        assert a.daughters[1].entity == 'b-type@b-type_le'
        assert a.daughters[1].basic_entity() == 'b-type'

    def test_lexical_type(self):
        # NOTE: this returns None for standard UDF or non-preterminals
        a = D.from_string('(root (1 a-type -1 -1 -1 ("a"))'
                          '      (2 b-type -1 -1 -1 ("b")))')
        assert a.lexical_type() == None
        assert a.daughters[0].lexical_type() == None
        assert a.daughters[1].lexical_type() == None
        a = D.from_string('(root (1 a-type@a-type_le -1 -1 -1 ("a"))'
                          '      (2 b-type@b-type_le -1 -1 -1 ("b")))')
        assert a.lexical_type() == None
        assert a.daughters[0].lexical_type() == 'a-type_le'
        assert a.daughters[1].lexical_type() == 'b-type_le'


# from delphin.derivation import Derivation

# import unittest

# class derivation_test(unittest.TestCase):

#     def setUp(self):
#         # ACE output text
#         self.ace_output_text = "tree 1 #T[1 \"LABEL\" \"TOKEN\" 2 RULE_NAME]"
#         self.ace_output_text2 = "tree 1 #T[1 \"LABEL\" \"TOKEN\" 2 RULE_NAME] \"TOKEN\""
#         # Terminal text
#         self.terminal_text = "#T[1 \"LABEL\" \"TOKEN\" 2 RULE_NAME]"
#         self.terminal_text2 = "#T[10 \"LABEL\" \"TOKEN\" 34 RULE_NAME]"
#         self.terminal_text3 = "#T[485 \"LABEL\" \"TOKEN\" 9238 RULE_NAME]"
#         self.terminal_nil = "#T[1 \"LABEL\" nil 2 RULE_NAME]"
#         self.terminal_grammar_pred = "#T[1 LABEL \"TOKEN\" 2 RULE_NAME]"
#         self.terminal_punctuation = "#T[1 \"LABEL\" \"Don't.\" 2 RULE_NAME]"
#         # Unary text
#         self.unary_text = "#T[9 \"LABEL\" nil 93 RULE_NAME #T[10 \"LABEL2\" \"TOKEN\" 39 RULE_NAME2]]"
#         self.unary_text2 = "#T[39 \"LABEL\" nil 93 RULE_NAME #T[40 \"LABEL2\" \"TOKEN\" 20 RULE_NAME2] ]"
#         self.unary_text3 = "#T[93 \"LABEL\" nil 48 RULE_NAME #T[45 \"LABEL2\" \"TOKEN\" 234 RULE_NAME2] ]"
#         # Binary text
#         self.binary_text = "#T[9 \"LABEL\" nil 93 RULE_NAME #T[10 \"LABEL2\" \"TOKEN\" 39 RULE_NAME2] #T[11 \"LABEL3\" \"TOKEN2\" 240 RULE_NAME3]]"
#         self.binary_text2 = "#T[10 \"LABEL\" nil 29 RULE_NAME #T[11 \"LABEL2\" \"TOKEN\" 75 RULE_NAME2] #T[12 \"LABEL3\" \"TOKEN2\" 241 RULE_NAME3]]"
#         self.binary_text3 = "#T[1346 \"LABEL\" nil 2345 RULE_NAME #T[25 \"LABEL2\" \"TOKEN\" 55 RULE_NAME2] #T[234 \"LABEL3\" \"TOKEN2\" 248 RULE_NAME3]]"
#         # Ternary text
#         self.ternary_text = "#T[9 \"LABEL\" nil 93 RULE_NAME #T[10 \"LABEL2\" \"TOKEN\" 39 RULE_NAME2] #T[11 \"LABEL3\" \"TOKEN2\" 240 RULE_NAME3] #T[12 \"LABEL4\" \"TOKEN3\" 340 RULE_NAME4]]"
#         self.ternary_text2 = "#T[10 \"LABEL\" nil 94 RULE_NAME #T[11 \"LABEL2\" \"TOKEN\" 40 RULE_NAME2] #T[12 \"LABEL3\" \"TOKEN2\" 241 RULE_NAME3] #T[13 \"LABEL4\" \"TOKEN3\" 341 RULE_NAME4]]"
#         self.ternary_text3 = "#T[16 \"LABEL\" nil 95 RULE_NAME #T[12 \"LABEL2\" \"TOKEN\" 41 RULE_NAME2] #T[13 \"LABEL3\" \"TOKEN2\" 244 RULE_NAME3] #T[16 \"LABEL4\" \"TOKEN3\" 342 RULE_NAME4]]"
#         # Nested text
#         self.nested_text = "#T[1 'S' nil 3 subj-head #T[2 'NP' nil 93 spec-head #T[2 'D' 'the' 93 the_d1] #T[3 'N' 'man' 39 man_n1]] #T[3 'V' 'runs' 39 runs_v1]]"
#         self.nested_high_count = "#T[10 'S' nil 3 subj-head #T[20 'NP' nil 93 spec-head #T[20 'D' 'the' 93 the_d1] #T[30 'N' 'man' 39 man_n1]] #T[40 'V' 'runs' 39 runs_v1]]"
#         # Real text
#         self.ace_output = """ tree 1 #T[1 "S" nil 843 sb-hd_mc_c #T[2 "NP" nil 837 hdn_bnp-qnt_c #T[3 "NP" "I" 85 i]] #T[4 "VP" nil 842 hd-cmp_u_c #T[5 "V" nil 838 v_n3s-bse_ilr #T[6 "V" "like" 56 like_v1]] #T[7 "NP" nil 841 hdn_bnp_c #T[8 "N" nil 840 w_period_plr #T[9 "N" nil 839 n_pl_olr #T[10 "N" "dogs." 62 dog_n1]]]]]] "I like dogs.\""""

#     def test_nested_text(self):
#         tree = Derivation(self.nested_text)
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "S")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "3")
#         self.assertTrue(tree.rule_name == "subj-head")
#         self.assertTrue(len(tree.children) == 2)
#         # Child 1
#         child = tree.children[0]
#         self.assertTrue(child.edge_ID == "2")
#         self.assertTrue(child.label == "NP")
#         self.assertTrue(child.token == None)
#         self.assertTrue(child.chart_ID == "93")
#         self.assertTrue(child.rule_name == "spec-head")
#         self.assertTrue(len(child.children) == 2)
#         # Child 1a
#         child = child.children[0]
#         self.assertTrue(child.edge_ID == "2")
#         self.assertTrue(child.label == "D")
#         self.assertTrue(child.token == "the")
#         self.assertTrue(child.chart_ID == "93")
#         self.assertTrue(child.rule_name == "the_d1")
#         self.assertTrue(len(child.children) == 0)
#         # Child 1b
#         child = tree.children[0].children[1]
#         self.assertTrue(child.edge_ID == "3")
#         self.assertTrue(child.label == "N")
#         self.assertTrue(child.token == "man")
#         self.assertTrue(child.chart_ID == "39")
#         self.assertTrue(child.rule_name == "man_n1")
#         self.assertTrue(len(child.children) == 0)
#         # Child 2
#         child = tree.children[1]
#         self.assertTrue(child.edge_ID == "3")
#         self.assertTrue(child.label == "V")
#         self.assertTrue(child.token == "runs")
#         self.assertTrue(child.chart_ID == "39")
#         self.assertTrue(child.rule_name == "runs_v1")
#         self.assertTrue(len(child.children) == 0)

#     def test_high_count(self):
#         tree = Derivation(self.nested_high_count)
#         self.assertTrue(tree.edge_ID == "10")
#         self.assertTrue(tree.label == "S")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "3")
#         self.assertTrue(tree.rule_name == "subj-head")
#         self.assertTrue(len(tree.children) == 2)
#         # Child 1
#         child = tree.children[0]
#         self.assertTrue(child.edge_ID == "20")
#         self.assertTrue(child.label == "NP")
#         self.assertTrue(child.token == None)
#         self.assertTrue(child.chart_ID == "93")
#         self.assertTrue(child.rule_name == "spec-head")
#         self.assertTrue(len(child.children) == 2)
#         # Child 1a
#         child = child.children[0]
#         self.assertTrue(child.edge_ID == "20")
#         self.assertTrue(child.label == "D")
#         self.assertTrue(child.token == "the")
#         self.assertTrue(child.chart_ID == "93")
#         self.assertTrue(child.rule_name == "the_d1")
#         self.assertTrue(len(child.children) == 0)
#         # Child 1b
#         child = tree.children[0].children[1]
#         self.assertTrue(child.edge_ID == "30")
#         self.assertTrue(child.label == "N")
#         self.assertTrue(child.token == "man")
#         self.assertTrue(child.chart_ID == "39")
#         self.assertTrue(child.rule_name == "man_n1")
#         self.assertTrue(len(child.children) == 0)
#         # Child 2
#         child = tree.children[1]
#         self.assertTrue(child.edge_ID == "40")
#         self.assertTrue(child.label == "V")
#         self.assertTrue(child.token == "runs")
#         self.assertTrue(child.chart_ID == "39")
#         self.assertTrue(child.rule_name == "runs_v1")
#         self.assertTrue(len(child.children) == 0)

#     def test_read_ACE_output(self):
#         tree = Derivation(self.ace_output_text)
#         self.assertTrue(tree.tree_ID == "1")
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == "TOKEN")
#         self.assertTrue(tree.chart_ID == "2")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 0)

#     def test_read_ACE_output2(self):
#         tree = Derivation(self.ace_output_text2)
#         self.assertTrue(tree.tree_ID == "1")
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == "TOKEN")
#         self.assertTrue(tree.chart_ID == "2")
#         self.assertTrue(tree.rule_name == "RULE_NAME")

#     def test_read_ACE_terminal(self):
#         tree = Derivation(self.terminal_text)
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == "TOKEN")
#         self.assertTrue(tree.chart_ID == "2")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 0)

#     def test_read_ACE_terminal_nil(self):
#         tree = Derivation(self.terminal_nil)
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "2")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 0)

#     def test_read_ACE_terminal_grammar_pred(self):
#         tree = Derivation(self.terminal_grammar_pred)
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == "TOKEN")
#         self.assertTrue(tree.chart_ID == "2")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 0)

#     def test_read_ACE_terminal_punctuation(self):
#         tree = Derivation(self.terminal_punctuation)
#         self.assertEqual(tree.edge_ID, "1")
#         self.assertEqual(tree.label, "LABEL")
#         self.assertEqual(tree.token, "Don't.")
#         self.assertEqual(tree.chart_ID, "2")
#         self.assertEqual(tree.rule_name, "RULE_NAME")
#         self.assertEqual(len(tree.children), 0)

#     def test_read_ACE_unary(self):
#         tree = Derivation(self.unary_text)
#         self.assertTrue(tree.edge_ID == "9")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "93")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 1)
#         # Child 1
#         self.assertTrue(tree.children[0].edge_ID == "10")
#         self.assertTrue(tree.children[0].label == "LABEL2")
#         self.assertTrue(tree.children[0].token == "TOKEN")
#         self.assertTrue(tree.children[0].chart_ID == "39")
#         self.assertTrue(tree.children[0].rule_name == "RULE_NAME2")
#         self.assertTrue(len(tree.children[0].children) == 0)

#     def test_read_ACE_binary(self):
#         tree = Derivation(self.binary_text)
#         self.assertTrue(tree.edge_ID == "9")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "93")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 2)
#         # Child 1
#         self.assertTrue(tree.children[0].edge_ID == "10")
#         self.assertTrue(tree.children[0].label == "LABEL2")
#         self.assertTrue(tree.children[0].token == "TOKEN")
#         self.assertTrue(tree.children[0].chart_ID == "39")
#         self.assertTrue(tree.children[0].rule_name == "RULE_NAME2")
#         self.assertTrue(len(tree.children[0].children) == 0)
#         # Child 2
#         self.assertTrue(tree.children[1].edge_ID == "11")
#         self.assertTrue(tree.children[1].label == "LABEL3")
#         self.assertTrue(tree.children[1].token == "TOKEN2")
#         self.assertTrue(tree.children[1].chart_ID == "240")
#         self.assertTrue(tree.children[1].rule_name == "RULE_NAME3")
#         self.assertTrue(len(tree.children[1].children) == 0)

#     def test_read_ACE_ternary(self):
#         tree = Derivation(self.ternary_text)
#         self.assertTrue(tree.edge_ID == "9")
#         self.assertTrue(tree.label == "LABEL")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "93")
#         self.assertTrue(tree.rule_name == "RULE_NAME")
#         self.assertTrue(len(tree.children) == 3)
#         # Child 1
#         self.assertTrue(tree.children[0].edge_ID == "10")
#         self.assertTrue(tree.children[0].label == "LABEL2")
#         self.assertTrue(tree.children[0].token == "TOKEN")
#         self.assertTrue(tree.children[0].chart_ID == "39")
#         self.assertTrue(tree.children[0].rule_name == "RULE_NAME2")
#         self.assertTrue(len(tree.children[0].children) == 0)
#         # Child 2
#         self.assertTrue(tree.children[1].edge_ID == "11")
#         self.assertTrue(tree.children[1].label == "LABEL3")
#         self.assertTrue(tree.children[1].token == "TOKEN2")
#         self.assertTrue(tree.children[1].chart_ID == "240")
#         self.assertTrue(tree.children[1].rule_name == "RULE_NAME3")
#         self.assertTrue(len(tree.children[1].children) == 0)
#         # Child 3
#         self.assertTrue(tree.children[2].edge_ID == "12")
#         self.assertTrue(tree.children[2].label == "LABEL4")
#         self.assertTrue(tree.children[2].token == "TOKEN3")
#         self.assertTrue(tree.children[2].chart_ID == "340")
#         self.assertTrue(tree.children[2].rule_name == "RULE_NAME4")
#         self.assertTrue(len(tree.children[2].children) == 0)

#     def test_read_ACE_real(self):
#         tree = Derivation(self.ace_output)
#         self.assertTrue(tree.edge_ID == "1")
#         self.assertTrue(tree.label == "S")
#         self.assertTrue(tree.token == None)
#         self.assertTrue(tree.chart_ID == "843")
#         self.assertTrue(tree.rule_name == "sb-hd_mc_c")
#         self.assertEqual(len(tree.children), 2)
#         # Child 1
#         child1 = tree.children[0]
#         self.assertTrue(child1.edge_ID == "2")
#         self.assertTrue(child1.label == "NP")
#         self.assertTrue(child1.token == None)
#         self.assertTrue(child1.chart_ID == "837")
#         self.assertTrue(child1.rule_name == "hdn_bnp-qnt_c")
#         self.assertEqual(len(child1.children), 1)
#         # Child 1.a
#         child1a = child1.children[0]
#         self.assertTrue(child1a.edge_ID == "3")
#         self.assertTrue(child1a.label == "NP")
#         self.assertTrue(child1a.token == "I")
#         self.assertTrue(child1a.chart_ID == "85")
#         self.assertTrue(child1a.rule_name == "i")
#         self.assertEqual(len(child1a.children), 0)
#         # Child 2
#         child2 = tree.children[1]
#         self.assertTrue(child2.edge_ID == "4")
#         self.assertTrue(child2.label == "VP")
#         self.assertTrue(child2.token == None)
#         self.assertTrue(child2.chart_ID == "842")
#         self.assertTrue(child2.rule_name == "hd-cmp_u_c")
#         self.assertEqual(len(child2.children), 2)
#         # Child 2.a
#         child2a = child2.children[0]
#         self.assertTrue(child2a.edge_ID == "5")
#         self.assertTrue(child2a.label == "V")
#         self.assertTrue(child2a.token == None)
#         self.assertTrue(child2a.chart_ID == "838")
#         self.assertTrue(child2a.rule_name == "v_n3s-bse_ilr")
#         self.assertEqual(len(child2a.children), 1)
#         # Child 2.a.1
#         child2a1 = child2a.children[0]
#         self.assertTrue(child2a1.edge_ID == "6")
#         self.assertTrue(child2a1.label == "V")
#         self.assertTrue(child2a1.token == "like")
#         self.assertTrue(child2a1.chart_ID == "56")
#         self.assertTrue(child2a1.rule_name == "like_v1")
#         self.assertEqual(len(child2a1.children), 0)
#         # Child 2.b
#         child2b = child2.children[1]
#         self.assertTrue(child2b.edge_ID == "7")
#         self.assertTrue(child2b.label == "NP")
#         self.assertTrue(child2b.token == None)
#         self.assertTrue(child2b.chart_ID == "841")
#         self.assertTrue(child2b.rule_name == "hdn_bnp_c")
#         self.assertEqual(len(child2b.children), 1)
#         # Child 2.b.1
#         child2b1 = child2b.children[0]
#         self.assertTrue(child2b1.edge_ID == "8")
#         self.assertTrue(child2b1.label == "N")
#         self.assertTrue(child2b1.token == None)
#         self.assertTrue(child2b1.chart_ID == "840")
#         self.assertTrue(child2b1.rule_name == "w_period_plr")
#         self.assertEqual(len(child2b1.children), 1)
#         # Child 2.b.1.a
#         child2b1a = child2b1.children[0]
#         self.assertTrue(child2b1a.edge_ID == "9")
#         self.assertTrue(child2b1a.label == "N")
#         self.assertTrue(child2b1a.token == None)
#         self.assertTrue(child2b1a.chart_ID == "839")
#         self.assertTrue(child2b1a.rule_name == "n_pl_olr")
#         self.assertEqual(len(child2b1a.children), 1)
#         # Child 2.b.1.a.1
#         child2b1a1 = child2b1a.children[0]
#         self.assertTrue(child2b1a1.edge_ID == "10")
#         self.assertTrue(child2b1a1.label == "N")
#         self.assertTrue(child2b1a1.token == "dogs.")
#         self.assertTrue(child2b1a1.chart_ID == "62")
#         self.assertTrue(child2b1a1.rule_name == "dog_n1")
#         self.assertEqual(len(child2b1a1.children), 0)

#     ## Test output methods
#     def test_output_HTML_terminal(self):
#         expected = '''<div class="derivationTree"><ul><li class="terminal" id=2 title="2: RULE_NAME"><p>LABEL</p><p>TOKEN</p></li></ul></div>'''
#         self.assertEqual(Derivation(self.terminal_text).output_HTML(), expected)

#     def test_output_HTML_unary(self):
#         expected = '''<div class="derivationTree"><ul><li id=93 title="93: RULE_NAME"><p>LABEL</p><ul><li class="terminal" id=39 title="39: RULE_NAME2"><p>LABEL2</p><p>TOKEN</p></li></ul></li></ul></div>'''
#         self.assertEqual(Derivation(self.unary_text).output_HTML(), expected)

#     def test_output_HTML_binary(self):
#         expected = '''<div class="derivationTree"><ul><li id=93 title="93: RULE_NAME"><p>LABEL</p><ul><li class="terminal" id=39 title="39: RULE_NAME2"><p>LABEL2</p><p>TOKEN</p></li><li class="terminal" id=240 title="240: RULE_NAME3"><p>LABEL3</p><p>TOKEN2</p></li></ul></li></ul></div>'''
#         self.assertEqual(Derivation(self.binary_text).output_HTML(), expected)

#     def test_output_HTML_ACE(self):
#         expected = '''<div class="derivationTree" id="1"><ul><li class="terminal" id=2 title="2: RULE_NAME"><p>LABEL</p><p>TOKEN</p></li></ul></div>'''
#         self.assertEqual(Derivation(self.ace_output_text).output_HTML(), expected)

#     ## Test equals methods
#     # Terminal
#     def test_equals_reflexive_terminal(self):
#         tree = Derivation(self.terminal_text)
#         self.assertTrue(tree == tree)

#     def test_equals_symmetric_terminal(self):
#         tree = Derivation(self.terminal_text)
#         tree2 = Derivation(self.terminal_text2)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree)

#     def test_equals_transitive_terminal(self):
#         tree = Derivation(self.terminal_text)
#         tree2 = Derivation(self.terminal_text2)
#         tree3 = Derivation(self.terminal_text3)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree3)
#         self.assertTrue(tree3 == tree)

#     def test_equals_consistent_terminal(self):
#         tree = Derivation(self.terminal_text)
#         tree2 = Derivation(self.terminal_text2)
#         for _ in range(10):
#             self.assertTrue(tree == tree2)

#     def test_equals_none_terminal(self):
#         tree = Derivation(self.terminal_text)
#         self.assertFalse(tree == None)

#     # Unary
#     def test_equals_reflexive_unary(self):
#         tree = Derivation(self.unary_text)
#         self.assertTrue(tree == tree)

#     def test_equals_symmetric_unary(self):
#         tree = Derivation(self.unary_text)
#         tree2 = Derivation(self.unary_text2)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree)

#     def test_equals_transitive_unary(self):
#         tree = Derivation(self.unary_text)
#         tree2 = Derivation(self.unary_text2)
#         tree3 = Derivation(self.unary_text3)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree3)
#         self.assertTrue(tree3 == tree)

#     def test_equals_consistent_unary(self):
#         tree = Derivation(self.unary_text)
#         tree2 = Derivation(self.unary_text2)
#         for _ in range(10):
#             self.assertTrue(tree == tree2)

#     def test_equals_none_unary(self):
#         tree = Derivation(self.unary_text)
#         self.assertFalse(tree == None)

#     # Binary
#     def test_equals_reflexive_binary(self):
#         tree = Derivation(self.binary_text)
#         self.assertTrue(tree == tree)

#     def test_equals_symmetric_binary(self):
#         tree = Derivation(self.binary_text)
#         tree2 = Derivation(self.binary_text2)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree)

#     def test_equals_transitive_binary(self):
#         tree = Derivation(self.binary_text)
#         tree2 = Derivation(self.binary_text2)
#         tree3 = Derivation(self.binary_text3)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree3)
#         self.assertTrue(tree3 == tree)

#     def test_equals_consistent_binary(self):
#         tree = Derivation(self.binary_text)
#         tree2 = Derivation(self.binary_text2)
#         for _ in range(10):
#             self.assertTrue(tree == tree2)

#     def test_equals_none_binary(self):
#         tree = Derivation(self.binary_text)
#         self.assertFalse(tree == None)

#     # Ternary
#     def test_equals_reflexive_ternary(self):
#         tree = Derivation(self.ternary_text)
#         self.assertTrue(tree == tree)

#     def test_equals_symmetric_ternary(self):
#         tree = Derivation(self.ternary_text)
#         tree2 = Derivation(self.ternary_text2)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree)

#     def test_equals_transitive_ternary(self):
#         tree = Derivation(self.ternary_text)
#         tree2 = Derivation(self.ternary_text2)
#         tree3 = Derivation(self.ternary_text3)
#         self.assertTrue(tree == tree2)
#         self.assertTrue(tree2 == tree3)
#         self.assertTrue(tree3 == tree)

#     def test_equals_consistent_ternary(self):
#         tree = Derivation(self.ternary_text)
#         tree2 = Derivation(self.ternary_text2)
#         for _ in range(10):
#             self.assertTrue(tree == tree2)

#     def test_equals_none_ternary(self):
#         tree = Derivation(self.ternary_text)
#         self.assertFalse(tree == None)



