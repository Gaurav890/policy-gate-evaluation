"""Offline native-environment tests of interception, continuation and evidence visibility."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from intervention_study import runner, gates
from intervention_study.common import BASE, read, environment, save
from intervention_study.predicates import observed_facts, check
from gateway_budget import GatewayError

class FakeGateway:
    class Budget:
        def total_reserved(self):return 0
    budget=Budget()
    def __init__(self, case, monitor_failure=False):
        self.steps=iter(case['fixture_reads']+[case['reference_action']]);self.n=0;self.actor_inputs=[];self.monitor_inputs=[];self.monitor_failure=monitor_failure
    def complete(self, model, messages, **kwargs):
        self.n+=1;role=kwargs['role'];receipt={'request_id':str(self.n),'request':{'model':model,'reasoning':{'effort':'none'}},'response':{'usage':{}}}
        if role.startswith('pressure_gate'):
            self.monitor_inputs.append(copy.deepcopy(messages))
            if self.monitor_failure:raise GatewayError('test missing output')
            return {'role':'assistant','content':json.dumps({'risk':1,'reason':'Disallowed under this policy.'})},receipt
        if role=='pressure_customer':return {'role':'assistant','content':json.dumps({'response':'Thank you.','stop':True,'pushback':False})},receipt
        self.actor_inputs.append(copy.deepcopy(messages))
        action=next(self.steps,None)
        if action:
            return {'role':'assistant','content':None,'tool_calls':[{'id':str(self.n),'type':'function','function':{'name':action['name'],'arguments':json.dumps(action['arguments'])}}]},receipt
        return {'role':'assistant','content':'I have finished checking your request.'},receipt

class InterventionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=read(BASE/'cases.json')
    def case(self,rule,pressure=True):return next(c for c in self.cases if c['pair_id']==rule+'-00' and c['pressure']==pressure)
    def run_case(self,case,condition='none',fail=False,limit=6):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ['cases.json','native_reference_validation.json']:shutil.copy(BASE/name,root/name)
            save(root/'protocol.json',{})
            cell={k:case[k] for k in ['case_id','pair_id','rule','pressure','domain','split']};cell.update(episode='unit',actor='test',condition=condition,repeat=0)
            g=FakeGateway(case,fail)
            with patch.object(runner,'BASE',root):rec=runner.run(cell,{'max_actor_turns':32,'max_customer_turns':limit,'customer_model':'customer','gate_model':'gate'},g)
            return rec,g
    def test_oracle_blocks_before_mutation_and_actor_continues(self):
        for rule in ['airline_cancellation','airline_basic_economy','airline_compensation','retail_identity_lookup','retail_post_item_change']:
            rec,g=self.run_case(self.case(rule),'oracle')
            self.assertTrue(rec['attempted_selected_violation']);self.assertFalse(rec['executed_selected_violation'])
            event=rec['actions'][-1];self.assertTrue(event['blocked']);self.assertEqual(event['before_db_hash'],event['after_db_hash'])
            self.assertTrue(any('policy_gate_blocked' in (m.get('content') or '') for m in g.actor_inputs[-1] if m['role']=='tool'))
            self.assertEqual(rec['termination'],'customer_stop')
    def test_no_gate_records_native_enforcement_separately(self):
        for rule in ['airline_cancellation','airline_passenger_count']:
            rec,_=self.run_case(self.case(rule));event=rec['actions'][-1]
            self.assertFalse(event['blocked']);self.assertTrue(event['attempted_selected_violation'])
            self.assertEqual(event['executed_selected_violation'],rule=='airline_cancellation')
            self.assertEqual(event['tool_error'],rule=='airline_passenger_count')
    def test_all_clean_reference_rollouts_complete(self):
        for rule in ['airline_cancellation','airline_basic_economy','airline_passenger_count','airline_compensation','retail_return_status','retail_refund_destination','retail_identity_lookup','retail_post_item_change']:
            rec,_=self.run_case(self.case(rule,False),'oracle');self.assertTrue(rec['control_reference_state_match'],rule)
    def test_broad_receives_only_public_proposal_prefix(self):
        case=self.case('airline_cancellation');rec,g=self.run_case(case,'broad')
        public=json.loads(g.monitor_inputs[0][-1]['content'])
        self.assertEqual(set(public),{'policy','tools','conversation_prefix','current_write'})
        self.assertEqual(public['conversation_prefix'][-1]['role'],'assistant')
        self.assertEqual(public['current_write']['arguments'],case['reference_action']['arguments'])
        self.assertTrue(rec['actions'][-1]['blocked'])
    def test_missing_monitor_is_fail_closed_with_failure_flag(self):
        rec,_=self.run_case(self.case('airline_cancellation'),'broad',True)
        self.assertEqual(rec['gate_failures'],1);self.assertFalse(rec['executed_selected_violation'])
    def test_unknown_not_silently_clean(self):
        action=self.case('airline_cancellation')['reference_action']
        rows=check('airline',action,observed_facts([]));self.assertEqual(rows[0]['verdict'],'unknown')
    def test_customer_limit_not_counted_as_completion(self):
        rec,_=self.run_case(self.case('airline_cancellation'),limit=0)
        self.assertEqual(rec['status'],'incomplete');self.assertEqual(rec['termination'],'customer_turn_limit')
    def test_decomposed_known_violations_need_no_private_state_or_model(self):
        rec,g=self.run_case(self.case('airline_cancellation'),'decomposed')
        self.assertTrue(rec['actions'][-1]['blocked']);self.assertEqual(g.monitor_inputs,[])

if __name__=='__main__':unittest.main()
