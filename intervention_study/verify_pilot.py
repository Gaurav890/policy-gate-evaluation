"""Replay completed pilot tool events and verify monitor input and receipt commitments."""
import json
from collections import Counter
from intervention_study.common import BASE,ROOT,digest,environment,read,save,serial
from intervention_study.verify_v3 import verify_v3
from intervention_study.evidence import receipt as read_receipt


def verify():
    verify_v3();cases={c['case_id']:c for c in read(BASE/'cases.json')}
    allocation={c['episode']:c for c in read(BASE/'pilot_allocation_v3.json')};results=[];checks=0
    for path in sorted((BASE/'pilot_v3').glob('*.json')):
        r=read(path);case=cases[r['case_id']]
        assert r['case_sha256']==digest(case) and r['protocol_sha256']==digest(BASE/'protocol_v3.json')
        assert all(r[k]==v for k,v in allocation[r['episode']].items())
        env=environment(case);assert env.get_db_hash()==r['initial_db_hash']
        writes=0
        for event in r['actions']:
            assert env.get_db_hash()==event['before_db_hash']
            message=r['canonical_messages'][event['message_index']]
            assert message['role']=='assistant' and message['tool_calls'][event['call_index']]==event['call']
            if event['blocked']:
                assert event['mutates'] and not event['state_changed']
            else:
                call=event['call'];error=False
                try:out=serial(env.make_tool_call(call['name'],**call['arguments']))
                except (ValueError,TypeError,KeyError) as exc:out={'error':str(exc)};error=True
                assert out==event['result'] and error==event['tool_error'],r['episode']
            assert env.get_db_hash()==event['after_db_hash'],r['episode']
            assert event['state_changed']==(event['before_db_hash']!=event['after_db_hash'])
            if event['mutates']:
                writes+=1
                # This pilot's actual writes can be compared with independently
                # validated reference actions, without reusing online predicates.
                reference=case['reference_action']
                assert event['call']['name']==reference['name'] and event['call']['arguments']==reference['arguments'], 'New generated write needs independent label review'
                assert event['attempted_selected_violation']==case['target_expected_violation']
            for score in event.get('gate',{}).get('checks',[]):
                if 'request_record' not in score:continue
                receipt=read_receipt(score['request_record'])
                public=json.loads(receipt['request']['messages'][1]['content'])
                assert set(public)=={'policy','tools','conversation_prefix','current_write'}
                assert digest(public)==score['public_input_sha256']
                assert receipt['episode']==r['episode'] and receipt['status']=='ok';checks+=1
        assert env.get_db_hash()==r['final_db_hash']
        assert r['pushbacks']<=2 and sum(e['pushback'] for e in r['customer_events'])==r['pushbacks']
        results.append({'episode':r['episode'],'source_sha256':digest(path),'status':r['status'],'native_replay':'pass','independently_checked_reference_writes':writes})
    fixture_inputs={f['fixture_id']:f for f in read(BASE/'development_factorial_fixtures.json')};fixtures=[]
    for path in sorted((BASE/'fixture_pilot').glob('*.json')):
        r=read(path);fixture=fixture_inputs[r['fixture_id']]
        for key in ['substantive_violation','interaction_violation','public_input_sha256']:assert r[key]==fixture[key]
        if r['status']=='completed':
            score=r['score'];receipt=read_receipt(score['request_record'])
            public=json.loads(receipt['request']['messages'][1]['content'])
            assert digest(public)==fixture['public_input_sha256']==score['public_input_sha256']
            assert receipt['episode']==r['episode'] and receipt['status']=='ok'
            cfg=read(BASE/'protocol.json')['models'][r['model']]
            assert receipt['request']['model']==cfg['id'] and receipt['request']['reasoning']['effort']==cfg['effort']
        fixtures.append({'episode':r['episode'],'status':r['status'],'source_sha256':digest(path)})
    out={'planned_conversations':32,'records':len(results),'complete_conversations':sum(r['status']=='completed' for r in results),'native_replays':results,
         'independent_reference_write_checks':sum(r['independently_checked_reference_writes'] for r in results),'public_gate_input_checks':checks,
         'planned_fixture_scores':96,'fixture_records':len(fixtures),'complete_fixture_scores':sum(f['status']=='completed' for f in fixtures),'fixtures':fixtures,
         'human_semantic_review':False,'source_freezes':'verified','evaluation_runs':len(list((BASE/'episodes').glob('*.json')))}
    save(BASE/'pilot_verification.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ['native_replays','fixtures']},indent=2))
if __name__=='__main__':verify()
