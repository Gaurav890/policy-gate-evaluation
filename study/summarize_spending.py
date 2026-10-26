"""Read-only reported-charge summary; does not infer bills for unresolved attempts."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json

def main():
    records=[json.loads(p.read_text()) for p in (ROOT/'groundwork/api_records').glob('*.json')]
    groups=defaultdict(lambda:{'requests':0,'reported_cost_usd':0.0,'unresolved_reserved_usd':0.0})
    for r in records:
        role=r.get('role','');episode=r.get('episode','')
        group='heldout_monitor' if role=='confirmatory_monitor' else 'policy_ablation' if role=='policy_ablation' else 'heldout_actor_and_customer' if episode.startswith('heldout-') else 'development_and_setup'
        g=groups[group];g['requests']+=1;cost=r.get('response',{}).get('usage',{}).get('cost')
        if cost is None:g['unresolved_reserved_usd']+=r['reserved_usd']
        else:g['reported_cost_usd']+=float(cost)
    total=sum(g['reported_cost_usd'] for g in groups.values());unknown=sum(g['unresolved_reserved_usd'] for g in groups.values())
    result={'authorized_cumulative_cap_usd':30,'requests':len(records),'response_status_counts':dict(Counter(r['status'] for r in records)),
       'reported_cost_usd':total,'unresolved_reserved_usd':unknown,'conservative_held_usd':1.25*total+unknown,
       'groups':dict(groups),'interpretation':'Response-reported charges; one legacy HTTP 429 has no resolved billing receipt and retains its reservation. Not a provider invoice.'}
    write_json(ROOT/'study/spending.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
