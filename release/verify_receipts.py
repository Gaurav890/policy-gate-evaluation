"""Audit the added monitor requests and cumulative response-reported costs offline."""
import hashlib,json,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from substantive_evaluation.monitor import windows
from gateway_budget import MODELS

def main():
 cfg=json.loads((R/'substantive_evaluation/monitor_protocol.json').read_text());checked=0
 MODELS.update(json.loads((R/'substantive_evaluation/protocol.json').read_text())['models'])
 roots=[R/'groundwork/api_records',R/'substantive_evaluation/api_records']
 receipts={}
 for root in roots:
  for p in root.glob('*.json'):
   assert p.stem not in receipts,p.name
   receipts[p.stem]=p
 def record(rid):return json.loads(receipts[rid].read_text())
 for folder in cfg['cohorts']:
  for p in (R/folder).glob('*.json'):
   e=json.loads(p.read_text())
   if e['status']!='completed':continue
   for v in windows(e):
    for model in cfg['models']:
     for target in cfg['targets']:
      s=json.loads((R/f"substantive_evaluation/scores/{model}/{target}/{e['episode']}--event-{v['event_index']:03}.json").read_text())
      ids=[s['request_record']] if s['status']=='scored' else s['attempt_records']
      assert ids
      for rid in ids:
       q=record(rid);req=q['request']
       assert req['messages'][0]['content']==cfg['prompts'][target]
       assert json.loads(req['messages'][1]['content'])==v['input']
       assert req['model']==MODELS[model]['id']
      if s['status']=='scored':
       answer=json.loads(q['response']['choices'][0]['message']['content'])
       assert answer['risk']==s['risk'] and answer['reason']==s['reason']
      checked+=1
 spend=json.loads((R/'substantive_evaluation/spending.json').read_text())
 costs=[]
 for p in receipts.values():
  q=json.loads(p.read_text());cost=q.get('response',{}).get('usage',{}).get('cost')
  if cost is not None:costs.append(float(cost))
 total=math.fsum(costs)
 assert len(receipts)==sum(g['requests'] for g in spend['groups'].values())
 assert math.isclose(total,spend['reported_cumulative_usd'],rel_tol=0,abs_tol=1e-8)
 out={'added_monitor_cells_checked':checked,'api_records':len(receipts),'response_reported_cost_usd':total,'cost_tolerance_usd':1e-8,'provider_invoice':False,'network_model_calls':0}
 (R/'release/receipt_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
