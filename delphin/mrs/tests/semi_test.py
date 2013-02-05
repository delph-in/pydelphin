from ..semi import Vpm
import unittest

class TestVpm(unittest.TestCase):
    def setUp(self):
        # simple just maps A:a1 <> X:x1
        self.simple = Vpm(mappings=[
            (('A',),('X',),[(('a1',),'<>',('x1',))])])
        # many_r has multiple right-side targets: A:a1 <> X:x1 Y:y1
        self.many_r = Vpm(mappings=[
            (('A',),('X','Y'),[(('a1',),'<>',('x1','y1'))])])
        # many_l has multiple left-side sources: A:a1 B:b1 <> X:x1
        self.many_l = Vpm(mappings=[
            (('A','B'),('X',),[(('a1','b1'),'<>',('x1',))])])
        # many_lr has multiple sources and targets: A:a1 B:b1 <> X:x1 Y:y1
        self.many_lr = Vpm(mappings=[
            (('A','B'),('X','Y'),[(('a1','b1'),'<>',('x1','y1'))])])

    def test_find_map(self):
        props1 = {'A':'a1', 'B':'b1'}
        props2 = {'A':'a2', 'B':'b2'}
        rev_props1 = {'X':'x1', 'Y':'y1'}
        rev_props2 = {'X':'x2', 'Y':'y2'}
        fm = self.simple.find_map
        self.assertEqual(fm(props1, ('A',)), {'X':'x1'})
        self.assertEqual(fm(props2, ('A',)), {'A':'a2'})
        self.assertEqual(fm(rev_props1, ('X',), reverse=True), {'A':'a1'})
        self.assertEqual(fm(rev_props2, ('X',), reverse=True), {'X':'x2'})
