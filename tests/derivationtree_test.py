from delphin.derivations.derivationtree import Derivation

import unittest

class derivationtree_test(unittest.TestCase):

    def setUp(self):
        # Terminal text
        self.terminal_text = "#T[1 \"LABEL\" \"TOKEN\" 2 RULE_NAME]'"
        self.terminal_text2 = "#T[10 \"LABEL\" \"TOKEN\" 34 RULE_NAME]'"
        self.terminal_text3 = "#T[485 \"LABEL\" \"TOKEN\" 9238 RULE_NAME]'"
        self.terminal_nil = "#T[1 \"LABEL\" nil 2 RULE_NAME]'"
        self.terminal_grammar_pred = "#T[1 LABEL \"TOKEN\" 2 RULE_NAME]'"
        # Unary text
        self.unary_text = "#T[9 \"LABEL\" nil 93 RULE_NAME #T[10 \"LABEL2\" \"TOKEN\" 39 RULE_NAME2]]"
        self.unary_text2 = "#T[39 \"LABEL\" nil 93 RULE_NAME #T[40 \"LABEL2\" \"TOKEN\" 20 RULE_NAME2] ]"
        self.unary_text3 = "#T[93 \"LABEL\" nil 48 RULE_NAME #T[45 \"LABEL2\" \"TOKEN\" 234 RULE_NAME2] ]"
        # Binary text
        self.binary_text = "#T[9 \"LABEL\" nil 93 RULE_NAME #T[10 \"LABEL2\" \"TOKEN\" 39 RULE_NAME2] #T[11 \"LABEL3\" \"TOKEN2\" 240 RULE_NAME3]]"
        self.binary_text2 = "#T[10 \"LABEL\" nil 29 RULE_NAME #T[11 \"LABEL2\" \"TOKEN\" 75 RULE_NAME2] #T[12 \"LABEL3\" \"TOKEN2\" 241 RULE_NAME3]]"
        self.binary_text3 = "#T[1346 \"LABEL\" nil 2345 RULE_NAME #T[25 \"LABEL2\" \"TOKEN\" 55 RULE_NAME2] #T[234 \"LABEL3\" \"TOKEN2\" 248 RULE_NAME3]]"
        # Ternary text
        self.ternary_text = "#T[9 \"LABEL\" nil 93 RULE_NAME #T[10 \"LABEL2\" \"TOKEN\" 39 RULE_NAME2] #T[11 \"LABEL3\" \"TOKEN2\" 240 RULE_NAME3] #T[12 \"LABEL4\" \"TOKEN3\" 340 RULE_NAME4]]"
        self.ternary_text2 = "#T[10 \"LABEL\" nil 94 RULE_NAME #T[11 \"LABEL2\" \"TOKEN\" 40 RULE_NAME2] #T[12 \"LABEL3\" \"TOKEN2\" 241 RULE_NAME3] #T[13 \"LABEL4\" \"TOKEN3\" 341 RULE_NAME4]]"
        self.ternary_text3 = "#T[16 \"LABEL\" nil 95 RULE_NAME #T[12 \"LABEL2\" \"TOKEN\" 41 RULE_NAME2] #T[13 \"LABEL3\" \"TOKEN2\" 244 RULE_NAME3] #T[16 \"LABEL4\" \"TOKEN3\" 342 RULE_NAME4]]"

    def test_read_ACE_terminal(self):
        tree = Derivation(self.terminal_text)
        self.assertTrue(tree.edge_ID == "1")
        self.assertTrue(tree.label == "LABEL")
        self.assertTrue(tree.token == "TOKEN")
        self.assertTrue(tree.chart_ID == "2")
        self.assertTrue(tree.rule_name == "RULE_NAME")
        self.assertTrue(len(tree.children) == 0)

    def test_read_ACE_terminal_nil(self):
        tree = Derivation(self.terminal_nil)
        self.assertTrue(tree.edge_ID == "1")
        self.assertTrue(tree.label == "LABEL")
        self.assertTrue(tree.token == None)
        self.assertTrue(tree.chart_ID == "2")
        self.assertTrue(tree.rule_name == "RULE_NAME")
        self.assertTrue(len(tree.children) == 0)

    def test_read_ACE_terminal_grammar_pred(self):
        tree = Derivation(self.terminal_grammar_pred)
        self.assertTrue(tree.edge_ID == "1")
        self.assertTrue(tree.label == "LABEL")
        self.assertTrue(tree.token == "TOKEN")
        self.assertTrue(tree.chart_ID == "2")
        self.assertTrue(tree.rule_name == "RULE_NAME")
        self.assertTrue(len(tree.children) == 0)

    def test_read_ACE_unary(self):
        tree = Derivation(self.unary_text)
        self.assertTrue(tree.edge_ID == "9")
        self.assertTrue(tree.label == "LABEL")
        self.assertTrue(tree.token == None)
        self.assertTrue(tree.chart_ID == "93")
        self.assertTrue(tree.rule_name == "RULE_NAME")
        self.assertTrue(len(tree.children) == 1)
        # Child 1
        self.assertTrue(tree.children[0].edge_ID == "10")
        self.assertTrue(tree.children[0].label == "LABEL2")
        self.assertTrue(tree.children[0].token == "TOKEN")
        self.assertTrue(tree.children[0].chart_ID == "39")
        self.assertTrue(tree.children[0].rule_name == "RULE_NAME2")
        self.assertTrue(len(tree.children[0].children) == 0)
        
    def test_read_ACE_binary(self):
        tree = Derivation(self.binary_text)
        self.assertTrue(tree.edge_ID == "9")
        self.assertTrue(tree.label == "LABEL")
        self.assertTrue(tree.token == None)
        self.assertTrue(tree.chart_ID == "93")
        self.assertTrue(tree.rule_name == "RULE_NAME")
        self.assertTrue(len(tree.children) == 2)
        # Child 1
        self.assertTrue(tree.children[0].edge_ID == "10")
        self.assertTrue(tree.children[0].label == "LABEL2")
        self.assertTrue(tree.children[0].token == "TOKEN")
        self.assertTrue(tree.children[0].chart_ID == "39")
        self.assertTrue(tree.children[0].rule_name == "RULE_NAME2")
        self.assertTrue(len(tree.children[0].children) == 0)
        # Child 2
        self.assertTrue(tree.children[1].edge_ID == "11")
        self.assertTrue(tree.children[1].label == "LABEL3")
        self.assertTrue(tree.children[1].token == "TOKEN2")
        self.assertTrue(tree.children[1].chart_ID == "240")
        self.assertTrue(tree.children[1].rule_name == "RULE_NAME3")
        self.assertTrue(len(tree.children[1].children) == 0)
        
    def test_read_ACE_ternary(self):
        tree = Derivation(self.ternary_text)
        self.assertTrue(tree.edge_ID == "9")
        self.assertTrue(tree.label == "LABEL")
        self.assertTrue(tree.token == None)
        self.assertTrue(tree.chart_ID == "93")
        self.assertTrue(tree.rule_name == "RULE_NAME")
        self.assertTrue(len(tree.children) == 3)
        # Child 1
        self.assertTrue(tree.children[0].edge_ID == "10")
        self.assertTrue(tree.children[0].label == "LABEL2")
        self.assertTrue(tree.children[0].token == "TOKEN")
        self.assertTrue(tree.children[0].chart_ID == "39")
        self.assertTrue(tree.children[0].rule_name == "RULE_NAME2")
        self.assertTrue(len(tree.children[0].children) == 0)
        # Child 2
        self.assertTrue(tree.children[1].edge_ID == "11")
        self.assertTrue(tree.children[1].label == "LABEL3")
        self.assertTrue(tree.children[1].token == "TOKEN2")
        self.assertTrue(tree.children[1].chart_ID == "240")
        self.assertTrue(tree.children[1].rule_name == "RULE_NAME3")
        self.assertTrue(len(tree.children[1].children) == 0)
        # Child 3
        self.assertTrue(tree.children[2].edge_ID == "12")
        self.assertTrue(tree.children[2].label == "LABEL4")
        self.assertTrue(tree.children[2].token == "TOKEN3")
        self.assertTrue(tree.children[2].chart_ID == "340")
        self.assertTrue(tree.children[2].rule_name == "RULE_NAME4")
        self.assertTrue(len(tree.children[2].children) == 0)

    ## Test output methods
    def test_get_HTML_terminal(self):
        expected = "<div id=2 title=\"2: RULE_NAME\"><p>LABEL</p><p>TOKEN</p></div>"
        self.assertEqual(Derivation(self.terminal_text).get_HTML(), expected)

    def test_get_HTML_unary(self):
        expected = "<div id=93 title=\"93: RULE_NAME\"><p>LABEL</p><div id=39 title=\"39: RULE_NAME2\"><p>LABEL2</p><p>TOKEN</p></div></div>"
        self.assertEqual(Derivation(self.unary_text).get_HTML(), expected)

    def test_get_HTML_binary(self):
        expected = "<div id=93 title=\"93: RULE_NAME\"><p>LABEL</p><div id=39 title=\"39: RULE_NAME2\"><p>LABEL2</p><p>TOKEN</p></div> <div id=240 title=\"240: RULE_NAME3\"><p>LABEL3</p><p>TOKEN2</p></div></div>"
        self.assertEqual(Derivation(self.binary_text).get_HTML(), expected)

    ## Test equals methods
    # Terminal
    def test_equals_reflexive_terminal(self):
        tree = Derivation(self.terminal_text)
        self.assertTrue(tree == tree)
 
    def test_equals_symmetric_terminal(self):
        tree = Derivation(self.terminal_text)
        tree2 = Derivation(self.terminal_text2)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree)

    def test_equals_transitive_terminal(self):
        tree = Derivation(self.terminal_text)
        tree2 = Derivation(self.terminal_text2)
        tree3 = Derivation(self.terminal_text3)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree3)
        self.assertTrue(tree3 == tree)

    def test_equals_consistent_terminal(self):
        tree = Derivation(self.terminal_text)
        tree2 = Derivation(self.terminal_text2)
        for _ in range(10):
            self.assertTrue(tree == tree2)
        
    def test_equals_none_terminal(self):
        tree = Derivation(self.terminal_text)
        self.assertFalse(tree == None)

    # Unary
    def test_equals_reflexive_unary(self):
        tree = Derivation(self.unary_text)
        self.assertTrue(tree == tree)
 
    def test_equals_symmetric_unary(self):
        tree = Derivation(self.unary_text)
        tree2 = Derivation(self.unary_text2)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree)

    def test_equals_transitive_unary(self):
        tree = Derivation(self.unary_text)
        tree2 = Derivation(self.unary_text2)
        tree3 = Derivation(self.unary_text3)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree3)
        self.assertTrue(tree3 == tree)

    def test_equals_consistent_unary(self):
        tree = Derivation(self.unary_text)
        tree2 = Derivation(self.unary_text2)
        for _ in range(10):
            self.assertTrue(tree == tree2)
        
    def test_equals_none_unary(self):
        tree = Derivation(self.unary_text)
        self.assertFalse(tree == None)

    # Binary
    def test_equals_reflexive_binary(self):
        tree = Derivation(self.binary_text)
        self.assertTrue(tree == tree)
 
    def test_equals_symmetric_binary(self):
        tree = Derivation(self.binary_text)
        tree2 = Derivation(self.binary_text2)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree)

    def test_equals_transitive_binary(self):
        tree = Derivation(self.binary_text)
        tree2 = Derivation(self.binary_text2)
        tree3 = Derivation(self.binary_text3)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree3)
        self.assertTrue(tree3 == tree)

    def test_equals_consistent_binary(self):
        tree = Derivation(self.binary_text)
        tree2 = Derivation(self.binary_text2)
        for _ in range(10):
            self.assertTrue(tree == tree2)
        
    def test_equals_none_binary(self):
        tree = Derivation(self.binary_text)
        self.assertFalse(tree == None)

    # Ternary
    def test_equals_reflexive_ternary(self):
        tree = Derivation(self.ternary_text)
        self.assertTrue(tree == tree)
 
    def test_equals_symmetric_ternary(self):
        tree = Derivation(self.ternary_text)
        tree2 = Derivation(self.ternary_text2)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree)

    def test_equals_transitive_ternary(self):
        tree = Derivation(self.ternary_text)
        tree2 = Derivation(self.ternary_text2)
        tree3 = Derivation(self.ternary_text3)
        self.assertTrue(tree == tree2)
        self.assertTrue(tree2 == tree3)
        self.assertTrue(tree3 == tree)

    def test_equals_consistent_ternary(self):
        tree = Derivation(self.ternary_text)
        tree2 = Derivation(self.ternary_text2)
        for _ in range(10):
            self.assertTrue(tree == tree2)
        
    def test_equals_none_ternary(self):
        tree = Derivation(self.ternary_text)
        self.assertFalse(tree == None)


    
