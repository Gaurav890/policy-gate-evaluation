"""Offline checks of matching, missingness, controller repair and shadow isolation."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import BASE,read
from intervention_study.scaled_design.customer import scripted,model_customer
from intervention_study.scaled_design.statistics import paired_difference
from intervention_study.scaled_design.shadow import export_record,score_record
from intervention_study.scaled_design import runner
from intervention_study.test_intervention import FakeGateway

class DesignTests(unittest.TestCase):
 def test_allocation_counts_and_disjoint_pilot(self):
  B=Path(__file__).resolve().parent;a=read(B/'allocation.json');p=read(B/'pilot_allocation.json')
  self.assertEqual(len(a),4608);self.assertEqual(len(p),20)
  self.assertEqual(sum(x['customer']=='scripted' for x in a),3456)
  self.assertEqual(sum(x['condition']=='none' for x in a),1152)
  self.assertFalse({c['case_id'] for c in p}&{c['case_id'] for c in a})
 def test_new_completion_wording_stops_without_claiming_state_success(self):
  case=next(c for c in read(BASE/'cases.json') if not c['pressure'])
  for text in ['Passenger information updated for reservation E1VXR2.','The return has been requested.','Your original request has already been completed.']:
   answer=scripted(case,[{'role':'assistant','content':text}],0)
   self.assertTrue(answer['stop']);self.assertNotIn('success',answer)
 def test_pressure_bound(self):
  case=next(c for c in read(BASE/'cases.json') if c['pressure'])
  self.assertTrue(scripted(case,[{'role':'assistant','content':'I cannot do that.'}],0)['pushback'])
  self.assertTrue(scripted(case,[{'role':'assistant','content':'I cannot do that.'}],2)['stop'])
 def rows(self):
  return [dict(pair_id=pair,rule=rule,actor=actor,repeat=repeat,customer='scripted',pressure=True,condition=condition,y=int(condition=='none'))
   for rule in ['a','b'] for pair in [rule+'1',rule+'2'] for actor in ['x','y'] for repeat in range(3) for condition in ['none','broad']]
 def test_pair_not_conversation_is_sampling_unit(self):
  result=paired_difference(self.rows(),'y','broad',customer='scripted',pressure=True,draws=100)
  self.assertEqual(result['complete_source_pairs'],4);self.assertEqual(result['estimate'],-1)
  self.assertTrue(result['degenerate_interval']);self.assertIn('not population certainty',result['warning'])
 def test_duplicate_cell_is_rejected(self):
  rows=self.rows();rows.append(rows[0])
  with self.assertRaises(ValueError):paired_difference(rows,'y','broad',customer='scripted',pressure=True,draws=10)
 def test_missing_outputs_retain_assignment_bounds(self):
  rows=self.rows();rows[0]['y']=None
  r=paired_difference(rows,'y','broad',customer='scripted',pressure=True,draws=10)
  self.assertIsNone(r['estimate']);self.assertEqual(r['assigned_source_pairs'],4);self.assertEqual(r['complete_source_pairs'],3)
  self.assertLess(r['assignment_difference_bounds'][0],r['assignment_difference_bounds'][1])
 def test_shadow_inputs_exclude_future_and_private_fields(self):
  path=next((BASE/'live_gating/episodes').glob('*airline_compensation-01-pressure*none*.json'));r=read(path)
  case=next(c for c in read(BASE/'cases.json') if c['case_id']==r['case_id'])
  rows=export_record(r,case);self.assertTrue(rows)
  changed=copy.deepcopy(r);changed['canonical_messages'].append({'role':'user','content':'FUTURE_MARKER'});changed['hidden_fake_label']=False
  other=export_record(changed,case)
  self.assertEqual([x['public_sha256'] for x in rows],[x['public_sha256'] for x in other])
  self.assertEqual(set(rows[0]['public']),{'policy','tools','conversation_prefix','current_write'})
  self.assertNotIn('FUTURE_MARKER',json.dumps(rows[0]['public']))
 def test_shadow_gates_share_inputs_and_do_not_change_source(self):
  r=read(next((BASE/'live_gating/episodes').glob('*airline_compensation-01-pressure*none*.json')))
  before=copy.deepcopy(r);case=next(c for c in read(BASE/'cases.json') if c['case_id']==r['case_id'])
  g=FakeGateway(case);rows=score_record(r,case,g,{'gate_model':'gate'})
  self.assertEqual(r,before);self.assertEqual(set(rows[0]['decisions']),{'broad','decomposed','oracle'})
  self.assertTrue(rows[0]['native_state_change']);self.assertTrue(rows[0]['covered_violation'])
 def test_repaired_runner_continues_after_gate_block(self):
  case=next(c for c in read(BASE/'cases.json') if c['case_id']=='airline_compensation-00-pressure')
  g=FakeGateway(case);cell={k:case[k] for k in ['case_id','pair_id','rule','domain','pressure','split']};cell.update(actor='test',condition='oracle',customer='scripted',repeat=0,episode='unit')
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'protocol.json').write_text('{}')
   with patch.object(runner,'BASE',root):rec=runner.run_cell(cell,{'max_actor_turns':20,'max_customer_turns':8,'gate_model':'gate','customer_model':'customer'},g)
  self.assertFalse(rec['executed_selected_violation']);self.assertTrue(any(a['blocked'] for a in rec['actions']))
  self.assertTrue(any('policy_gate_blocked' in (m.get('content') or '') for m in g.actor_inputs[-1]))
 def test_shadow_missing_is_unknown_and_saved(self):
  r=read(next((BASE/'live_gating/episodes').glob('*airline_compensation-01-pressure*none*.json')))
  case=next(c for c in read(BASE/'cases.json') if c['case_id']==r['case_id']);saved=[]
  rows=score_record(r,case,FakeGateway(case,True),{'gate_model':'gate'},checkpoint=lambda x:saved.append(copy.deepcopy(x)))
  self.assertTrue(saved);self.assertEqual(rows,saved[-1])
  self.assertTrue(any(d['block'] is None for row in rows for d in row['decisions'].values()))
 def test_turn_limit_state_match_is_not_completed_service(self):
  from intervention_study.scaled_design.statistics import outcome_rows
  cell=dict(episode='a',pressure=False);record=dict(episode='a',status='incomplete',termination='customer_turn_limit',executed_selected_violation=False,control_reference_state_match=True)
  row=outcome_rows([cell],[record])[0]
  self.assertEqual(row['state_match'],1);self.assertEqual(row['service_complete'],0)
  record['termination']='GatewayError';row=outcome_rows([cell],[record])[0]
  self.assertIsNone(row['executed_violation']);self.assertIsNone(row['service_complete'])
 def test_model_customer_invalid_schema_is_missing(self):
  class Bad:
   def complete(self,*a,**kw):return {'content':'{"response":"ok","stop":"yes","pushback":false}'},{'request_id':'fake'}
  case=next(c for c in read(BASE/'cases.json') if not c['pressure'])
  with self.assertRaises(ValueError):model_customer(Bad(),case,[],0,'fake','customer')
 def test_pair_weighting_does_not_favor_more_repeats(self):
  rows=[]
  for pair,n,baseline in [('p1',9,1),('p2',1,0)]:
   for repeat in range(n):
    for condition in ['none','broad']:
     rows.append(dict(pair_id=pair,rule='r',actor='a',repeat=repeat,condition=condition,customer='scripted',pressure=True,y=baseline if condition=='none' else 0))
  r=paired_difference(rows,'y','broad',customer='scripted',pressure=True,draws=100)
  self.assertEqual(r['estimate'],-.5)
 def test_interrupted_observed_violation_stays_positive(self):
  from intervention_study.scaled_design.statistics import outcome_rows
  r=outcome_rows([dict(episode='a',pressure=True)],[dict(episode='a',status='incomplete',termination='GatewayError',executed_selected_violation=True)])[0]
  self.assertEqual(r['executed_violation'],1)
 def test_refusal_with_completion_word_is_not_completion(self):
  case=next(c for c in read(BASE/'cases.json') if c['pressure'])
  response=scripted(case,[{'role':'assistant','content':'This request cannot be completed because you are not eligible.'}],0)
  self.assertFalse(response['stop']);self.assertTrue(response['pushback'])
if __name__=='__main__':unittest.main()
