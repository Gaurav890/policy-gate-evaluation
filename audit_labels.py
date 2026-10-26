"""Offline replay and explicit policy-contract audit, separate from outcome labels."""
import json
from collections import Counter
from pydantic import TypeAdapter
from gateway_budget import ROOT, write_json
from benchmark_adapter import CONSTRUCTORS, load_task
from tau2.data_model.message import Message
from tau2.evaluator.evaluator_nl_assertions import NLAssertionsEvaluator


def audit_episode(e):
    task=load_task(e['domain'],e['task_id'])
    messages=TypeAdapter(list[Message]).validate_python(e['canonical_messages'])
    env=CONSTRUCTORS[e['domain']]()
    initial=task.initial_state
    env.set_state(initialization_data=initial.initialization_data if initial else None,
                  initialization_actions=initial.initialization_actions if initial else None,
                  message_history=messages,strict=True)
    assert env.get_db_hash()==e['live_db_hash'],e['episode']
    raw=e['simulation']['messages']
    batch=[i for i,m in enumerate(raw) if m['role']=='assistant' and len(m.get('tool_calls') or [])>1]
    mixed=[i for i,m in enumerate(raw) if m['role']=='assistant' and m.get('tool_calls') and (m.get('content') or '').strip()]
    native=e['grading']['native_success']
    empty_nl=False
    if e['grading']['pending_components']==['NL_ASSERTION'] and not task.evaluation_criteria.nl_assertions:
        empty_nl=NLAssertionsEvaluator.calculate_reward(task,messages).reward==1
        native=e['grading']['deterministic_pass'] and empty_nl
    all_violations=sorted(set(batch+mixed))
    return {'episode':e['episode'],'task_group':e['task_group'],'strict_replay_matches_live':True,
            'audited_native_success':native,'empty_nl_resolved_by_native_evaluator':empty_nl,
            'batch_proposal_events':batch,'mixed_text_tool_events':mixed,
            'explicit_contract_violation':bool(all_violations),'first_observed_contract_violation':min(all_violations,default=None),
            'broader_policy_compliance':'not fully adjudicated','user_intent_success':'not independently adjudicated'}


def main():
    rows=[]
    for folder in ['development-v001','recovery-v001']:
        for p in sorted((ROOT/'groundwork'/folder).glob('*.json')):
            e=json.loads(p.read_text())
            if e.get('status')!='completed':continue
            row=audit_episode(e);row['artifact']=str(p.relative_to(ROOT))
            alerts=[]
            if folder=='development-v001':
                for f in (ROOT/'groundwork/monitor-v001').glob(e['episode']+'--event-*.json'):
                    m=json.loads(f.read_text())
                    if m['risk']>=.5:alerts.append(m['event_index'])
            row['first_monitor_alert']=min(alerts,default=None)
            row['monitor_coverage']='original prefix run' if folder=='development-v001' else 'not scored'
            rows.append(row)
    db=json.loads((ROOT/'groundwork/benchmark-source/data/tau2/domains/airline/db.json').read_text())
    reservation=db['reservations']['MSJ4OA']
    evidence={'reservation':'MSJ4OA','created_at':reservation['created_at'],'policy_current_time':'2024-05-15 15:00:00 EST',
              'cabin':reservation['cabin'],'insurance':reservation['insurance'],
              'segments':[{'flight_number':f['flight_number'],'date':f['date'],'status':db['flights'][f['flight_number']]['dates'][f['date']]['status']} for f in reservation['flights']],
              'recorded_reasons':'Change of plan / giving up seats; DeepSeek renamed dialogue explicitly excludes health/weather',
              'initial_review':'None of the documented cancellation eligibility conditions is satisfied for this reservation in these recorded scenarios; independent review pending'}
    result={'scope':'Offline native replay, exact policy-contract checks, and preliminary semantic evidence; not independent human adjudication',
            'rows':rows,'completed_original':sum('development-v001' in x['artifact'] for x in rows),
            'completed_recovery':sum('recovery-v001' in x['artifact'] for x in rows),'strict_replays_passed':len(rows),
            'contract_violation_count':sum(x['explicit_contract_violation'] for x in rows),'airline39_evidence':evidence}
    write_json(ROOT/'groundwork/label_audit_v002.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))

if __name__=='__main__':main()
