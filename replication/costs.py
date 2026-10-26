"""Reconcile all local research requests without modifying historical reports."""
import json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json
from budget_reconciled import Budget
if __name__=='__main__':
 groups=defaultdict(lambda:{'requests':0,'reported_usd':0.,'unresolved_reserved_usd':0.})
 for line in (ROOT/'groundwork/spend_ledger.jsonl').read_text().splitlines():
  q=json.loads(line);p=ROOT/'groundwork/api_records'/(q['request_id']+'.json');r=json.loads(p.read_text()) if p.exists() else {};role=q['role'];ep=q['episode'];name='policy_monitor' if role.startswith('replication_policy') else 'expanded_monitor' if role.startswith('replication_monitor') else 'expanded_collection' if ep.startswith('rep-') else 'prior_research';g=groups[name];g['requests']+=1;cost=r.get('response',{}).get('usage',{}).get('cost')
  if cost is not None:g['reported_usd']+=float(cost)
  if cost is None or r.get('status')!='ok':g['unresolved_reserved_usd']+=q['reserved_usd']
 total=sum(g['reported_usd'] for g in groups.values());authorization=json.loads((ROOT/'groundwork/authorization.json').read_text());cap=authorization['cumulative_usd_cap']
 result={'groups':dict(groups),'cumulative_reported_usd':total,'new_reported_usd':total-groups['prior_research']['reported_usd'],'unresolved_reserved_usd':sum(g['unresolved_reserved_usd'] for g in groups.values()),'conservative_hold_usd':Budget(ceiling=cap).total_reserved(),'authorized_cap_usd':cap,'requests':sum(g['requests'] for g in groups.values()),'note':'Local response-reported accounting, not a provider invoice; reservations are admission holds, not additional charges.'}
 write_json(ROOT/'replication/spending.json',result);print(json.dumps(result,indent=2))
