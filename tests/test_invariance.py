import unittest
from monitor_invariance import cases,transform,structural_schema

class InvarianceTests(unittest.TestCase):
    def test_cases_have_reversible_inputs_and_same_argument_constraints(self):
        rows=cases()
        self.assertEqual(len(rows),16)
        self.assertEqual(len({r['task_group'] for r in rows}),4)
        for r in rows:
            for a,b in zip(r['original']['tools'],r['renamed']['tools']):
                self.assertEqual(structural_schema(a['function']['parameters']),structural_schema(b['function']['parameters']))
            self.assertEqual(len(r['original']['conversation_prefix']),len(r['renamed']['conversation_prefix']))
            self.assertEqual(set(r['original']),{'policy','tools','conversation_prefix'})
    def test_identifier_boundaries_and_data_structure_are_preserved(self):
        original={'content':'Use get_order_details; not fake_get_order_details_extra.', 'arguments':{'order_id':'#123'}}
        renamed=transform(original,{'get_order_details':'service_get_order_details'})
        self.assertEqual(renamed['arguments'],original['arguments'])
        self.assertEqual(renamed['content'],'Use service_get_order_details; not fake_get_order_details_extra.')

if __name__=='__main__':unittest.main()
