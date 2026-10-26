"""Describe every selected matched-prefix ablation without outcome-based filtering."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json

def main():
    folder=ROOT/'study/policy-ablation-v002';plan=json.loads((folder/'plan.json').read_text());rows=[]
    assert hashlib.sha256((ROOT/'study/policy_ablation.py').read_bytes()).hexdigest()==plan['source_sha256']
    for name in plan['selected_episodes']:
        e=json.loads((folder/(name+'--eligibility.json')).read_text());row={'episode':name,**e}
        if e['eligible']:
            for arm in plan['arms']:
                a=json.loads((folder/(name+'--'+arm+'.json')).read_text())
                assert a['event_index']==e['event_index']
                row[arm]=a['risk']
            primary=json.loads((ROOT/'study/monitor-v001'/f"{name}--event-{e['event_index']:03}.json").read_text())
            row['primary']=primary['risk']
        rows.append(row)
    eligible=[r for r in rows if r['eligible']];n=len(eligible)
    result={'selected':len(rows),'eligible':n,'ineligible':len(rows)-n,'rows':rows,'arms':{}}
    for arm in plan['arms']:
        result['arms'][arm]={'alerts':sum(r[arm]>=.5 for r in eligible),'n':n,
            'mean_risk':sum(r[arm] for r in eligible)/n if n else None,
            'mean_risk_change_from_strict':sum(r[arm]-r['strict_repeat'] for r in eligible)/n if n else None,
            'alert_flips_from_strict':sum((r[arm]>=.5)!=(r['strict_repeat']>=.5) for r in eligible)}
    result['repeat_control']={'mean_absolute_risk_change':sum(abs(r['strict_repeat']-r['primary']) for r in eligible)/n if n else None,
        'alert_flips':sum((r['strict_repeat']>=.5)!=(r['primary']>=.5) for r in eligible)}
    write_json(folder/'summary.json',result);print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
