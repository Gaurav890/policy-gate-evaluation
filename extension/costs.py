"""Extension accounting with the original frozen spend report preserved."""
import json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json

def main():
    old=json.loads((ROOT/'study/spending.json').read_text());groups=defaultdict(lambda:{'requests':0,'reported_usd':0.0,'unknown_reserved_usd':0.0})
    for p in (ROOT/'groundwork/api_records').glob('*.json'):
        r=json.loads(p.read_text());role=r.get('role','');ep=r.get('episode','')
        if role.startswith('extension_monitor_'):group=('original_second_monitor' if ep.startswith('heldout-') else 'extension_monitors')
        elif ep.startswith('ext-'):group='extension_actor_customer'
        else:group='original_study'
        g=groups[group];g['requests']+=1;cost=r.get('response',{}).get('usage',{}).get('cost')
        if cost is None:g['unknown_reserved_usd']+=r['reserved_usd']
        else:g['reported_usd']+=float(cost)
    total=sum(g['reported_usd'] for g in groups.values());unknown=sum(g['unknown_reserved_usd'] for g in groups.values())
    result={'groups':dict(groups),'total_reported_usd':total,'extension_reported_usd':total-old['reported_cost_usd'],'unknown_reserved_usd':unknown,'conservative_hold_usd':1.25*total+unknown,'authorized_cap_usd':30,'stage_ceiling_usd':26.54847889375,'requests':sum(g['requests'] for g in groups.values())}
    write_json(ROOT/'extension/spending.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
