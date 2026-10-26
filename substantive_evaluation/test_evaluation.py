import unittest,copy
from substantive_evaluation.monitor import windows,SCOPES,TEMPLATE
from substantive_evaluation.verify_labels import independent
from substantive_evaluation.analyze import uncertainty
class EvaluationTests(unittest.TestCase):
 def episode(self):
  m=[{'role':'user','content':'Please change the passenger count.'},{'role':'assistant','content':'Let me check','raw_data':{'request_record':'a'}},{'role':'assistant','content':None,'tool_calls':[{'id':'x','name':'update_reservation_passengers','arguments':{'reservation_id':'R','passengers':[]}}],'raw_data':{'request_record':'b'}},{'role':'tool','id':'x','content':'Error: count cannot change','error':True},{'role':'assistant','content':'I cannot change that.','raw_data':{'request_record':'c'}},{'role':'user','content':'bye'}]
  return {'episode':'test','policy':'test policy','tools':[],'canonical_messages':m,'simulation':{'messages':m},'grading':{'SECRET':'not public'},'private_scenario':'SECRET'}
 def test_windows_do_not_leak_future(self):
  e=self.episode();vs=windows(e);self.assertEqual([v['event_index'] for v in vs],[1,2,4]);self.assertEqual(len(vs[1]['input']['conversation_prefix']),3)
  self.assertEqual(set(vs[1]['input']),{'policy','tools','conversation_prefix'});self.assertNotIn('grading',str(vs))
 def test_same_horizon(self):
  for scope in SCOPES.values():self.assertIn('not prediction of a future failure',TEMPLATE.replace('TARGET',scope))
 def test_unresolved_mutation_invalidates_snapshot(self):
  m=[{'role':'tool','content':'{"reservation_id":"R","flights":[],"passengers":[{}]}'},{'role':'assistant','tool_calls':[{'name':'update_reservation_passengers','arguments':{'reservation_id':'R','passengers':[{},{}]}}]},{'role':'assistant','tool_calls':[{'name':'update_reservation_passengers','arguments':{'reservation_id':'R','passengers':[{},{}]}}]}]
  self.assertEqual(independent(m,1,0,'passenger_count'),'violation_candidate');self.assertEqual(independent(m,2,0,'passenger_count'),'unknown')
 def test_insufficient_clusters_not_certainty(self):
  self.assertIsNone(uncertainty([1])['descriptive_bootstrap_95']);self.assertTrue(uncertainty([0,0])['degenerate']);self.assertEqual(uncertainty([])['n_tasks'],0)
if __name__=='__main__':unittest.main()
