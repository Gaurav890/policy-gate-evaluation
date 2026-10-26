"""Verify frozen sources, task isolation and native state replay without API calls."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json
from benchmark_adapter import CONSTRUCTORS
from study.run_confirmatory import load_selected_task,make_audit_environment
from tau2.data_model.message import ToolCall
from pydantic import TypeAdapter
from tau2.data_model.message import Message


def main():
    plan=json.loads((ROOT/'study/confirmatory_manifest.json').read_text())
    checks=[]
    for file in ['study/confirmatory-v001/freeze.json','study/monitor-v001/freeze.json']:
        frozen=json.loads((ROOT/file).read_text())
        # Collector stores source hashes directly; monitor nests them.
        hashes=frozen.get('source_sha256',frozen)
        for name,digest in hashes.items():
            if not isinstance(digest,str) or len(digest)!=64:continue
            p=ROOT/name
            if p.is_file():
                assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
                checks.append(name)
    amendment=json.loads((ROOT/'study/execution_amendment.json').read_text())
    assert hashlib.sha256((ROOT/'study/run_airline_worker.py').read_bytes()).hexdigest()==amendment['worker_sha256']
    reference_checks=[]
    for row in plan['tasks']:
        task=load_selected_task(row['domain'],row['task_id'],plan)
        original,shifted=make_audit_environment(row['domain'],False),make_audit_environment(row['domain'],True)
        initial=task.initial_state
        for env in [original,shifted]:
            env.set_state(initial.initialization_data if initial else None,initial.initialization_actions if initial else None,initial.message_history or [] if initial else [])
        for i,action in enumerate(task.evaluation_criteria.actions or []):
            one=ToolCall(id=str(i),name=action.name,arguments=action.arguments,requestor=action.requestor)
            two=one.model_copy(deep=True)
            if two.requestor=='assistant':two.name=shifted.name_map[two.name]
            a,b=original.get_response(one),shifted.get_response(two)
            assert a.content==b.content and a.error==b.error
            assert original.get_db_hash()==shifted.get_db_hash()
        reference_checks.append({'task_group':row['task_group'],'actions':len(task.evaluation_criteria.actions or []),'responses_errors_and_states_match':True})
    rows=[]
    for path in sorted((ROOT/'study/confirmatory-v001').glob('heldout-*.json')):
        e=json.loads(path.read_text())
        if e['status']!='completed':continue
        task=load_selected_task(e['domain'],e['task_id'],plan)
        messages=TypeAdapter(list[Message]).validate_python(e['canonical_messages'])
        env=CONSTRUCTORS[e['domain']]();initial=task.initial_state
        env.set_state(initialization_data=initial.initialization_data if initial else None,
                      initialization_actions=initial.initialization_actions if initial else None,
                      message_history=messages,strict=True)
        assert env.get_db_hash()==e['live_db_hash'],e['episode']
        rows.append({'episode':e['episode'],'strict_replay_matches_live':True,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    assert len(rows)==48,'Incomplete primary collection'
    result={'strict_replays_passed':len(rows),'source_hashes_checked':sorted(set(checks)),
        'worker_hash_matches':True,'reference_equivalence':reference_checks,'rows':rows}
    write_json(ROOT/'study/analysis/replay_audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
if __name__=='__main__':main()
