"""Replay native writes, independently check labels, and audit gate visibility."""
import json
from collections import Counter
from intervention_study.common import BASE,read,save,digest,environment
from intervention_study.serialization import to_json
from intervention_study.verify_breadth_results import labels
from intervention_study.live_gating.verify_freeze import verify
from intervention_study.live_gating.records import receipt
RUNBASE=BASE/'live_gating'

def verify_results():
    verify();allocation={c['episode']:c for c in read(RUNBASE/'allocation.json')}
    cases={c['case_id']:c for c in read(BASE/'cases.json')};records=[];writes=public_checks=0
    for path in sorted((RUNBASE/'episodes').glob('*.json')):
        r=read(path);case=cases[r['case_id']]
        assert all(r[k]==v for k,v in allocation[r['episode']].items())
        assert r['case_sha256']==digest(case)
        assert r['protocol_sha256']==digest(RUNBASE/'protocol.json')
        env=environment(case);authenticated=set()
        assert r['initial_db_hash']==env.get_db_hash()
        for event in r['actions']:
            call=event['call'];assert env.get_db_hash()==event['before_db_hash']
            message=r['canonical_messages'][event['message_index']]
            assert message['tool_calls'][event['call_index']]==call
            if event['mutates']:
                expected=labels(case,call,env.tools.db.model_dump(mode='json'),authenticated)
                assert expected=={x['rule']:x['verdict'] for x in event['oracle_checks']},(r['episode'],expected,event['oracle_checks'])
                assert event['attempted_selected_violation']==('violation' in expected.values());writes+=1
            if event['blocked']:
                assert event['mutates'] and event['tool_error'] and not event['state_changed']
                assert event['gate']['block'] and event['result']['policy_gate_blocked']
            else:
                try:out=to_json(env.make_tool_call(call['name'],**call['arguments']));error=False
                except (ValueError,TypeError,KeyError) as exc:out={'error':str(exc)};error=True
                assert event['result']==out and event['tool_error']==error,r['episode']
                if call['name'].startswith('find_user_id_by_') and not error:authenticated.add(out)
            assert env.get_db_hash()==event['after_db_hash']
            assert event['state_changed']==(event['before_db_hash']!=event['after_db_hash'])
            assert event['executed_selected_violation']==(event['attempted_selected_violation'] and event['state_changed'])
            for score in event.get('gate',{}).get('checks',[]):
                if 'request_record' not in score:continue
                q=receipt(score['request_record']);public=json.loads(q['request']['messages'][1]['content'])
                assert q['episode']==r['episode'] and q['status']=='ok'
                assert set(public)=={'policy','tools','conversation_prefix','current_write'}
                assert digest(public)==score['public_input_sha256']
                assert public['current_write']==call and public['policy']==env.policy
                prefix=public['conversation_prefix'];assert prefix==r['canonical_messages'][:len(prefix)]
                assert q['request']['model']==score['requested_model'];public_checks+=1
        assert env.get_db_hash()==r['final_db_hash']
        assert r['executed_selected_violation']==any(a['executed_selected_violation'] for a in r['actions'])
        assert r['pushbacks']<=2
        records.append({'episode':r['episode'],'status':r['status'],'sha256':digest(path),'native_replay':'pass'})
    out={'planned':len(allocation),'records':len(records),'statuses':dict(Counter(r['status'] for r in records)),
        'independent_write_labels':writes,'public_gate_inputs_verified':public_checks,'native_replays':records,
        'scope':'Separate implementation of eight literal constraints plus native replay; no human semantic review.'}
    save(RUNBASE/'verification.json',out)
    print(json.dumps({k:v for k,v in out.items() if k!='native_replays'},indent=2))

if __name__=='__main__':verify_results()
