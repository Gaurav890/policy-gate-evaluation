"""Offline collection/score provenance checks, with optional native replay."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json
from run_monitors import prefix_views

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native',action='store_true');a=parser.parse_args()
    for name,h in json.loads((ROOT/'extension/collection_freeze.json').read_text()).items():assert digest(ROOT/name)==h,name
    original=json.loads((ROOT/'study/confirmatory_manifest.json').read_text());plan=json.loads((ROOT/'extension/plan.json').read_text());pilot=json.loads((ROOT/'pilot_manifest.json').read_text())
    assert not {r['task_group'] for r in original['tasks']}&{r['task_group'] for r in plan['tasks']}
    for domain in ['retail','airline']:
        old={r['task_id'] for r in original['tasks'] if r['domain']==domain}
        ids=[t for t in pilot['domains'][domain]['reserved_upstream_test_ids'] if t not in old]
        ranked=sorted(ids,key=lambda tid:hashlib.sha256(('extension-clean-v1:'+domain+':'+tid).encode()).hexdigest())[:3]
        assert ranked==[r['task_id'] for r in plan['tasks'] if r['domain']==domain]
    episodes=[]
    for p in sorted((ROOT/'extension/episodes').glob('*.json')):
        e=json.loads(p.read_text());assert e['status']=='completed';episodes.append(e)
    assert len(episodes)==24
    replay=[]
    if a.native:
        from pydantic import TypeAdapter
        from tau2.data_model.message import Message
        from benchmark_adapter import CONSTRUCTORS
        from study.run_confirmatory import load_selected_task
        for e in episodes:
            task=load_selected_task(e['domain'],e['task_id'],plan);initial=task.initial_state;env=CONSTRUCTORS[e['domain']]()
            messages=TypeAdapter(list[Message]).validate_python(e['canonical_messages'])
            env.set_state(initialization_data=initial.initialization_data if initial else None,initialization_actions=initial.initialization_actions if initial else None,message_history=messages,strict=True)
            assert env.get_db_hash()==e['live_db_hash']
            replay.append({'episode':e['episode'],'matches':True,'sha256':digest(ROOT/'extension/episodes'/(e['episode']+'.json'))})
        write_json(ROOT/'extension/replay.json',{'matched':len(replay),'rows':replay})
    counts={'scored':0,'missing':0}
    for freeze in (ROOT/'extension/monitors').glob('*/*/freeze.json'):
        for name,h in json.loads(freeze.read_text())['sources'].items():assert digest(ROOT/name)==h,name
        for p in freeze.parent.glob('*--event-*.json'):
            m=json.loads(p.read_text());counts[m['status']]+=1
            cohort=p.parents[1].name;folder='study/confirmatory-v001' if cohort=='original' else 'extension/episodes'
            e=json.loads((ROOT/folder/(m['episode']+'.json')).read_text());v=next(v for v in prefix_views(e) if v['event_index']==m['event_index'])
            assert hashlib.sha256(json.dumps(v['input'],sort_keys=True).encode()).hexdigest()==m['public_input_sha256']
            if m['status']=='scored':
                r=json.loads((ROOT/'groundwork/api_records'/(m['request_record']+'.json')).read_text())
                assert json.loads(r['request']['messages'][1]['content'])==v['input']
                answer=json.loads(r['response']['choices'][0]['message']['content']);assert answer['risk']==m['risk']
    print(json.dumps({'collection_freeze':'passed','allocation':'six new deterministic task IDs','episodes':len(episodes),'monitor_records':counts,'native_replays_this_run':len(replay)},indent=2))
if __name__=='__main__':main()
