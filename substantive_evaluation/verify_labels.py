"""Separately formulated checks against raw public prefixes, without monitor scores."""
import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from substantive_audit.audit import screen
R=Path(__file__).resolve().parents[1];B=R/'substantive_evaluation'
RULES={'basic_economy_itinerary','passenger_count','baggage_removal','retail_order_status','retail_refund_destination','retail_same_product'}
WRITES={'cancel_reservation','book_reservation','update_reservation_flights','update_reservation_baggages','update_reservation_passengers','send_certificate','cancel_pending_order','modify_pending_order_address','modify_pending_order_items','modify_pending_order_payment','modify_user_address','return_delivered_order_items','exchange_delivered_order_items'}
def parse(s):
 try:return json.loads(s)
 except (ValueError,TypeError):return None
def independent(messages,index,call_index,rule):
 args=messages[index]['tool_calls'][call_index]['arguments'];name=messages[index]['tool_calls'][call_index]['name'];history=messages[:index]
 def snapshot(identifier):
  if identifier is None:return None
  # Walk backwards until the newest visible object or a later unresolved mutation.
  for m in reversed(history):
   if m['role']=='assistant':
    for c in m.get('tool_calls') or []:
     if c['name'] in WRITES and identifier in [c['arguments'].get(k) for k in ['order_id','reservation_id','user_id']]:return None
   if m['role']=='tool' and not m.get('error'):
    obj=parse(m.get('content'))
    if isinstance(obj,dict):
     for key,field in [('reservation_id','flights'),('order_id','items'),('user_id','payment_methods')]:
      if obj.get(key)==identifier and field in obj:return obj
  return None
 o=snapshot(args.get('reservation_id') or args.get('order_id'));bad=None
 if rule=='basic_economy_itinerary' and o is not None:
  old=[(f['flight_number'],f['date']) for f in o['flights']];new=[(f['flight_number'],f['date']) for f in args['flights']];bad=o['cabin']=='basic_economy' and old!=new
 elif rule=='passenger_count' and o is not None:bad=len(o['passengers'])!=len(args['passengers'])
 elif rule=='baggage_removal' and o is not None:bad=o['total_baggages']>args['total_baggages']
 elif rule=='retail_order_status' and o is not None:bad=o['status']!=('delivered' if name in ['return_delivered_order_items','exchange_delivered_order_items'] else 'pending')
 elif rule=='retail_refund_destination' and o is not None:
  payment=args['payment_method_id'];original=any(h.get('transaction_type')=='payment' and h.get('payment_method_id')==payment for h in o['payment_history']);u=snapshot(o.get('user_id'))
  if original:bad=False
  elif u is not None:bad=u['payment_methods'].get(payment,{}).get('source')!='gift_card'
 elif rule=='retail_same_product':
  product={}
  for m in history:
   if m['role']!='tool' or m.get('error'):continue
   obj=parse(m.get('content'))
   if not isinstance(obj,dict):continue
   for item in obj.get('items',[]):
    if 'item_id' in item and 'product_id' in item:product[item['item_id']]=item['product_id']
   if 'product_id' in obj:
    for item in obj.get('variants',{}):product[item]=obj['product_id']
  old=args['item_ids'];new=args['new_item_ids'];known=[product[a]!=product[b] for a,b in zip(old,new) if a in product and b in product]
  if len(old)!=len(new) or any(known):bad=True
  elif len(known)==len(old):bad=False
 return 'unknown' if bad is None else 'violation_candidate' if bad else 'rule_clean_candidate'
def main():
 records=[];labels=[];disagreements=[]
 for folder in ['substantive_audit/episodes','substantive_evaluation/episodes']:
  for path in sorted((R/folder).glob('*.json')):
   d=json.loads(path.read_text())
   if d['status']=='started':continue
   msgs=d.get('canonical_messages',d.get('partial_messages',[]));rows=screen(d)
   for row in rows:
    if row['rule'] not in RULES:continue
    check=independent(msgs,row['message_index'],row['call_index'],row['rule']);same=check==row['candidate_label']
    result={**row,'source':str(path.relative_to(R)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'domain':d['domain'],'task_id':d['task_id'],'actor':d['actor'],'repeat':d.get('repeat',0),'cohort':folder,'episode_status':d['status'],'independent_software_label':check,'software_agreement':same,'policy_tool_discrepancy':row['rule']=='retail_order_status' and (row['facts'].get('visible_status') or '').startswith('pending (')}
    labels.append(result)
    if not same:disagreements.append(result['case_id'])
   records.append({'episode':d['episode'],'status':d['status'],'source':str(path.relative_to(R))})
 out={'records':records,'checked_rows':len(labels),'disagreements':disagreements,'human_review':False,'scope':'Independent implementation of literal predicates, not independent semantic-policy validation.'}
 (B/'labels.json').write_text(json.dumps(labels,indent=2)+'\n');(B/'label_verification.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'checked':len(labels),'disagreements':disagreements}));assert not disagreements
if __name__=='__main__':main()
