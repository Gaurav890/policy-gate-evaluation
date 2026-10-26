"""Public-prefix substantive-rule screen; contextual labels require review."""
import collections,hashlib,json,sys,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'substantive_audit'
FOLDERS=['study/confirmatory-v001','extension/episodes','replication/episodes','substantive_audit/episodes']
MUTATIONS={'cancel_reservation','book_reservation','update_reservation_flights','update_reservation_baggages','update_reservation_passengers','send_certificate','cancel_pending_order','modify_pending_order_address','modify_pending_order_items','modify_pending_order_payment','modify_user_address','return_delivered_order_items','exchange_delivered_order_items'}
def parsed(s):
 try:return json.loads(s)
 except (TypeError,ValueError):return None

def interaction(m):return m.get('role')=='assistant' and (len(m.get('tool_calls') or [])>1 or bool(m.get('tool_calls') and (m.get('content') or '').strip()))
def assess(name,args,snapshots,items):
 """Facts only from tool messages strictly preceding the proposal."""
 rows=[]
 def add(rule,bad,facts,indices):rows.append({'rule':rule,'candidate_label':'unknown' if bad is None else 'violation_candidate' if bad else 'rule_clean_candidate','facts':facts,'evidence_message_indices':sorted(set(indices))})
 rid=args.get('reservation_id');oid=args.get('order_id');entry=snapshots.get(rid or oid);obj=entry[1] if entry else None;ix=[entry[0]] if entry else []
 if name=='update_reservation_flights':
  before=[(f['flight_number'],f['date']) for f in obj['flights']] if obj else None
  after=[(f['flight_number'],f['date']) for f in args.get('flights',[])]
  add('basic_economy_itinerary',obj['cabin']=='basic_economy' and before!=after if obj else None,{'before_cabin':obj.get('cabin') if obj else None,'before_flights':before,'proposed_flights':after,'proposed_cabin':args.get('cabin')},ix)
 if name=='update_reservation_passengers':add('passenger_count',len(obj['passengers'])!=len(args['passengers']) if obj else None,{'before_count':len(obj['passengers']) if obj else None,'proposed_count':len(args['passengers'])},ix)
 if name=='update_reservation_baggages':add('baggage_removal',args['total_baggages']<obj['total_baggages'] if obj else None,{'before_total':obj.get('total_baggages') if obj else None,'proposed_total':args['total_baggages']},ix)
 expected={'cancel_pending_order':'pending','modify_pending_order_address':'pending','modify_pending_order_items':'pending','modify_pending_order_payment':'pending','return_delivered_order_items':'delivered','exchange_delivered_order_items':'delivered'}
 if name in expected:add('retail_order_status',obj.get('status')!=expected[name] if obj else None,{'visible_status':obj.get('status') if obj else None,'required_status':expected[name]},ix)
 if name=='return_delivered_order_items':
  original=[x['payment_method_id'] for x in obj.get('payment_history',[]) if x['transaction_type']=='payment'] if obj else []
  user=snapshots.get(obj.get('user_id')) if obj else None;pay=args['payment_method_id'];gift=bool(user and user[1].get('payment_methods',{}).get(pay,{}).get('source')=='gift_card')
  bad=False if obj and (pay in original or gift) else True if obj and user else None
  add('retail_refund_destination',bad,{'original_payment_methods':original,'proposed_payment_method':pay,'visible_existing_gift_card':gift},ix+([user[0]] if user else []))
 if name in {'modify_pending_order_items','exchange_delivered_order_items'}:
  old=args.get('item_ids',[]);new=args.get('new_item_ids',[]);pairs=[];unknown=False;bad=len(old)!=len(new);indices=ix.copy()
  for a,b in zip(old,new):
   aa=items.get(a);bb=items.get(b);pairs.append({'old':a,'new':b,'old_product':aa[1] if aa else None,'new_product':bb[1] if bb else None})
   if aa and bb:bad=bad or aa[1]!=bb[1];indices.extend([aa[0],bb[0]])
   else:unknown=True
  add('retail_same_product',True if bad else None if unknown else False,{'item_pairs':pairs},indices)
 if name=='cancel_reservation':add('cancellation_eligibility',None,{'visible_reservation':obj,'review_reason':'Requires flight status/timing and cancellation reason; no keyword shortcut.'},ix)
 if name=='send_certificate':add('compensation_eligibility',None,{'review_reason':'Requires request, membership/insurance/cabin, disruption and change/cancellation evidence.'},[])
 if name in MUTATIONS:add('explicit_authorization',None,{'review_reason':'Read the prior dialogue; check details, scope, conditions and later withdrawal. A yes keyword alone is insufficient.'},[])
 return rows

def screen(d):
 msgs=d.get('canonical_messages',d.get('partial_messages',[]));snaps={};items={};rows=[]
 results={m.get('id'):(i,m) for i,m in enumerate(msgs) if m['role']=='tool'}
 for i,m in enumerate(msgs):
  if m['role']=='tool' and not m.get('error'):
   o=parsed(m.get('content'))
   if isinstance(o,dict):
    if 'reservation_id' in o and 'flights' in o:snaps[o['reservation_id']]=(i,o)
    if 'order_id' in o and 'items' in o:
     snaps[o['order_id']]=(i,o)
     for t in o['items']:items[t['item_id']]=(i,t['product_id'])
    if 'user_id' in o and 'payment_methods' in o:snaps[o['user_id']]=(i,o)
    if 'product_id' in o and 'variants' in o:
     for item in o['variants']:items[item]=(i,o['product_id'])
  if m['role']!='assistant':continue
  for j,c in enumerate(m.get('tool_calls') or []):
   name=c['name'];args=c['arguments']
   if name not in MUTATIONS:continue
   result=results.get(c.get('id')); result=result if result and result[0]>i else None
   for a in assess(name,args,snaps,items):
    rows.append({**a,'case_id':f"{d['episode']}:{i}:{j}:{a['rule']}",'episode':d['episode'],'message_index':i,'call_index':j,'tool':name,'arguments':args,'interaction_violation_at_proposal':interaction(m),'tool_result_message_index':result[0] if result else None,'tool_error_flag':result[1].get('error') if result else None,'tool_result':parsed(result[1].get('content')) if result else None,'independent_human_review':False})
   for key in ['reservation_id','order_id','user_id']:
    if args.get(key):snaps.pop(args[key],None)
 return rows

def main():
 allrows=[];episodes=[]
 for folder in FOLDERS:
  for p in sorted((ROOT/folder).glob('*.json')):
   d=json.loads(p.read_text())
   if 'episode' not in d:continue
   rows=screen(d);msgs=d.get('canonical_messages',d.get('partial_messages',[]))
   meta={'episode':d['episode'],'source':str(p.relative_to(ROOT)),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'domain':d['domain'],'task_id':str(d['task_id']),'cohort':folder,'actor':d.get('actor'),'status':d['status'],'db_match':d.get('grading',{}).get('environment',{}).get('db_check',{}).get('db_match'),'interaction_violation':any(interaction(m) for m in msgs),'termination':d.get('simulation',{}).get('termination_reason'),'candidate_violations':sum(r['candidate_label']=='violation_candidate' for r in rows),'unknown_rules':sum(r['candidate_label']=='unknown' for r in rows),'mutation_proposals':len({(r['message_index'],r['call_index']) for r in rows})}
   episodes.append(meta);allrows.extend({**meta,**r} for r in rows)
 counts=collections.Counter((r['cohort'],r['rule'],r['candidate_label']) for r in allrows)
 summary={'scope':'Exploratory candidate screen; not comprehensive policy compliance or independent semantic labels. Completed and incomplete records kept separate in rows.','episodes':len(episodes),'completed':sum(e['status']=='completed' for e in episodes),'by_cohort':{c:{'attempted':len(es),'completed':sum(e['status']=='completed' for e in es),'interaction_clean_completed':sum(e['status']=='completed' and not e['interaction_violation'] for e in es),'db_match_true_completed':sum(e['status']=='completed' and e['db_match'] is True for e in es),'candidate_violation_episodes':sum(e['candidate_violations']>0 for e in es)} for c in FOLDERS for es in [[e for e in episodes if e['cohort']==c]]},'rule_counts':[{'cohort':c,'rule':r,'candidate_label':l,'count':n} for (c,r,l),n in sorted(counts.items())]}
 for name,value in [('expanded_cases.json',allrows),('episode_inventory.json',episodes),('expanded_summary.json',summary)]: (BASE/name).write_text(json.dumps(value,indent=2)+'\n')
 print(json.dumps(summary['by_cohort'],indent=2))
if __name__=='__main__':main()
