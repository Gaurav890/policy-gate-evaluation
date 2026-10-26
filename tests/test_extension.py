import unittest,json
from unittest.mock import patch
from extension.collect import ReminderGateway
from gateway_budget import ROOT
class ExtensionTests(unittest.TestCase):
    def test_reminder_changes_actor_only_and_preserves_input(self):
        gateway=object.__new__(ReminderGateway);gateway.reminder='ONE CALL'
        original=[{'role':'system','content':'policy'},{'role':'user','content':'task'}]
        with patch('gateway_v2.Gateway.complete',return_value='ok') as parent:
            gateway.complete('deepseek',original,role='actor');self.assertEqual(parent.call_args.args[1][0]['content'],'policy\n\nONE CALL')
            self.assertEqual(original[0]['content'],'policy')
            gateway.complete('claude',original,role='customer');self.assertEqual(parent.call_args.args[1],original)
    def test_allocation_is_new_and_balanced(self):
        new=json.loads((ROOT/'extension/plan.json').read_text());old=json.loads((ROOT/'study/confirmatory_manifest.json').read_text())
        self.assertFalse({x['task_group'] for x in new['tasks']}&{x['task_group'] for x in old['tasks']})
        self.assertEqual(len(new['tasks']),6)
        self.assertEqual(len(new['tasks'])*len(new['conditions'])*len(new['repeats']),24)

class ExtensionRateTests(unittest.TestCase):
    def test_unknown_score_creates_bounds_not_negative(self):
        from extension.analyze import rates
        rows=[{'state_success':True,'contract_violation':False,'monitors':{'m':{'any_alert':False,'any_identified':False}}},{'state_success':True,'contract_violation':False,'monitors':{'m':{'any_alert':True,'any_identified':True}}}]
        result=rates(rows,'m');self.assertEqual(result['lower'],.5);self.assertEqual(result['upper'],1.0)
    def test_no_clean_successes_is_undefined(self):
        from extension.analyze import rates
        result=rates([],'m');self.assertIsNone(result['lower']);self.assertIsNone(result['upper'])
