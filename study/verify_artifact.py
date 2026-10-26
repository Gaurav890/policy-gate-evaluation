"""Offline integrity checks; no benchmark dependency, credentials, or API calls."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT
from study.analyze_confirmatory import inventory
from run_monitors import prefix_views

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    checked=[]
    for rel in ['study/confirmatory-v001/freeze.json','study/monitor-v001/freeze.json']:
        f=json.loads((ROOT/rel).read_text());hashes=f.get('source_sha256',f)
        for name,h in hashes.items():
            assert digest(ROOT/name)==h,name
            checked.append(name)
    for rel,source in [('study/execution_amendment.json','study/run_airline_worker.py'),('study/monitor_execution_amendment.json','study/score_partitioned.py')]:
        f=json.loads((ROOT/rel).read_text());assert digest(ROOT/source)==f['worker_sha256'];checked.append(source)
    f=json.loads((ROOT/'study/monitor_missingness_amendment.json').read_text());assert digest(ROOT/f['source'])==f['source_sha256']
    f=json.loads((ROOT/'study/policy-ablation-v002/plan.json').read_text());assert digest(ROOT/'study/policy_ablation.py')==f['source_sha256']
    rows=inventory();assert len(rows)==48 and len({r['episode'] for r in rows})==48
    assert all(r['status']=='completed' and r['episode_metrics_identified'] for r in rows)
    analysis=json.loads((ROOT/'study/analysis/results.json').read_text());assert analysis['rows']==rows
    replay=json.loads((ROOT/'study/analysis/replay_audit.json').read_text());assert replay['strict_replays_passed']==48
    for row in replay['rows']:assert digest(ROOT/'study/confirmatory-v001'/(row['episode']+'.json'))==row['input_sha256']
    for path in (ROOT/'study/monitor-v001').glob('heldout-*.json'):
        m=json.loads(path.read_text());r=json.loads((ROOT/'groundwork/api_records'/(m['request_record']+'.json')).read_text())
        assert r['response']['choices'][0]['finish_reason']!='length'
        public=json.loads(r['request']['messages'][1]['content'])
        assert hashlib.sha256(json.dumps(public,sort_keys=True).encode()).hexdigest()==m['public_input_sha256']
        answer=json.loads(r['response']['choices'][0]['message']['content'])
        assert answer['risk']==m['risk'] and answer['reason']==m['reason']
    for path in (ROOT/'study/monitor-missing-v001').glob('heldout-*.json'):
        m=json.loads(path.read_text());assert not (ROOT/'study/monitor-v001'/path.name).exists()
        for rid in m['attempt_records']:
            r=json.loads((ROOT/'groundwork/api_records'/(rid+'.json')).read_text())
            assert r['response']['choices'][0]['finish_reason']=='length'
            public=json.loads(r['request']['messages'][1]['content']);assert len(public['conversation_prefix'])-1==m['event_index']
    for rel,h in json.loads((ROOT/'study/analysis/claim_ledger.json').read_text())['sources'].items():assert digest(ROOT/rel)==h,rel
    print(json.dumps({'verified':True,'source_freezes_checked':len(set(checked)),'replay_inputs_unchanged':48,
        'episode_metrics_identified':48,'scored_prefixes':analysis['scored_prefixes'],'missing_prefixes':analysis['missing_prefixes']},indent=2))
if __name__=='__main__':main()
