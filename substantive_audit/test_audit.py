import unittest
from substantive_audit.audit import assess,screen
class EvidenceTests(unittest.TestCase):
 def test_basic_change(self):
  old={'cabin':'basic_economy','flights':[{'flight_number':'A','date':'2024-05-20'}]}
  args={'reservation_id':'R','cabin':'economy','flights':[{'flight_number':'B','date':'2024-05-20'}]}
  self.assertEqual(assess('update_reservation_flights',args,{'R':(1,old)}, {})[0]['candidate_label'],'violation_candidate')
  args['flights']=old['flights'];self.assertEqual(assess('update_reservation_flights',args,{'R':(1,old)}, {})[0]['candidate_label'],'rule_clean_candidate')
 def test_future_facts_not_used(self):
  d={'episode':'test','canonical_messages':[{'role':'assistant','tool_calls':[{'name':'return_delivered_order_items','id':'x','arguments':{'order_id':'O','payment_method_id':'P'}}]},{'role':'tool','id':'x','content':'{"order_id":"O","status":"delivered","items":[]}'}]}
  rows=screen(d);self.assertTrue(all(r['candidate_label']=='unknown' for r in rows))
 def test_refund_unknown_not_violation(self):
  order={'user_id':'U','payment_history':[{'transaction_type':'payment','payment_method_id':'P'}],'status':'delivered'}
  args={'order_id':'O','payment_method_id':'G'}
  def label(snaps):return next(r for r in assess('return_delivered_order_items',args,snaps,{}) if r['rule']=='retail_refund_destination')['candidate_label']
  self.assertEqual(label({'O':(0,order)}),'unknown')
  self.assertEqual(label({'O':(0,order),'U':(1,{'payment_methods':{'G':{'source':'gift_card'}}})}),'rule_clean_candidate')
  self.assertEqual(label({'O':(0,order),'U':(1,{'payment_methods':{'G':{'source':'credit_card'}}})}),'violation_candidate')
 def test_cross_product_and_missing(self):
  args={'item_ids':['A'],'new_item_ids':['B']}
  def label(items):return next(r for r in assess('exchange_delivered_order_items',args,{},items) if r['rule']=='retail_same_product')['candidate_label']
  self.assertEqual(label({'A':(0,'shirt'),'B':(1,'shoe')}),'violation_candidate');self.assertEqual(label({'A':(0,'shirt')}),'unknown')
 def test_rejected_action_still_proposal(self):
  d={'episode':'x','canonical_messages':[{'role':'tool','id':'a','content':'{"order_id":"O","status":"cancelled","items":[]}'},{'role':'assistant','tool_calls':[{'id':'b','name':'cancel_pending_order','arguments':{'order_id':'O'}}]},{'role':'tool','id':'b','error':True,'content':'tool rejected'}]}
  row=screen(d)[0];self.assertEqual(row['candidate_label'],'violation_candidate');self.assertTrue(row['tool_error_flag'])
if __name__=='__main__':unittest.main()
