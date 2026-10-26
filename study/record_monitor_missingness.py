"""Register truncated primary-monitor responses without imputing their scores."""
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json
from run_monitors import prefix_views

def main():
    missing=defaultdict(list)
    for p in (ROOT/'groundwork/api_records').glob('*.json'):
        r=json.loads(p.read_text())
        if r.get('role')!='confirmatory_monitor':continue
        choices=r.get('response',{}).get('choices',[])
        if not choices or choices[0].get('finish_reason')!='length':continue
        public=json.loads(r['request']['messages'][1]['content']);event=len(public['conversation_prefix'])-1
        e=json.loads((ROOT/'study/confirmatory-v001'/(r['episode']+'.json')).read_text())
        view=next(v for v in prefix_views(e) if v['event_index']==event)
        assert view['input']==public
        missing[f"{r['episode']}--event-{event:03}"].append((r['utc'],r['request_id']))
    for key,ids in missing.items():
        # A later valid same-setting score would be a recorded recovery, not missing.
        if (ROOT/'study/monitor-v001'/(key+'.json')).exists():continue
        episode,event=key.rsplit('--event-',1)
        write_json(ROOT/'study/monitor-missing-v001'/(key+'.json'),{'episode':episode,'event_index':int(event),'status':'unscored',
            'reason':'truncated structured output at frozen 512 token cap','attempt_records':[rid for utc,rid in sorted(ids)],
            'treatment':'No imputed score; retain in coverage and identifiability checks'})
    print('Truncated prefix records:',len(missing))
if __name__=='__main__':main()
