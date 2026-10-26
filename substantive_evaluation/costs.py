"""Project-specific local accounting; response costs are not a provider invoice."""
import json,sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from budget_reconciled import Budget
R=Path(__file__).resolve().parents[1];B=R/'substantive_evaluation';groups=collections.defaultdict(lambda:{'requests':0,'reported_usd':0.,'unresolved_reserved_usd':0.,'errors':collections.Counter()})
for line in (R/'groundwork/spend_ledger.jsonl').read_text().splitlines():
 q=json.loads(line);p=R/'groundwork/api_records'/(q['request_id']+'.json');r=json.loads(p.read_text()) if p.exists() else {};name='new_monitor' if q.get('role','').startswith('substantive_monitor') else 'new_collection' if q.get('episode','').startswith('subeval-') else 'prior';g=groups[name];g['requests']+=1;cost=r.get('response',{}).get('usage',{}).get('cost')
 if cost is not None:g['reported_usd']+=float(cost)
 if cost is None or r.get('status')!='ok':g['unresolved_reserved_usd']+=q['reserved_usd'];g['errors'][str(r.get('http_status') or r.get('error_type') or r.get('status'))]+=1
out={'groups':dict(groups),'reported_cumulative_usd':sum(g['reported_usd'] for g in groups.values()),'new_reported_usd':sum(g['reported_usd'] for n,g in groups.items() if n!='prior'),'unresolved_reservations_usd':sum(g['unresolved_reserved_usd'] for g in groups.values()),'conservative_hold_usd':Budget(ceiling=100).total_reserved(),'authorized_ceiling_usd':100,'provider_invoice':False}
(B/'spending.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
