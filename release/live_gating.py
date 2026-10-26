"""Offline release adapter: original commitments and anonymized receipt hashes stay distinct.

This adapter leaves frozen collectors/analyses unchanged. --source is for the
private distributor; reviewers use the default or --native after unpacking.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
B=R/'intervention_study';L=B/'live_gating'
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value): p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def load_receipts(source=False):
    transformations={} if source else {x['file']:x for x in read(R/'release_transformations.json')['files']}
    groups={}
    for name,folder,ledger in [('preparation',B,'new_spend_ledger.jsonl'),('live_gating',L,'ledger.jsonl')]:
        meta=read(folder/'evidence/manifest.json')
        assert sha(folder/'evidence'/ledger)==meta['ledger_sha256']
        entries=[json.loads(x) for x in (folder/'evidence'/ledger).read_text().splitlines()]
        assert len(entries)==len({x['request_id'] for x in entries})==meta['record_count']
        assert {x['request_id'] for x in entries}==set(meta['records'])
        records={}
        for rid,original in meta['records'].items():
            if source:
                path=R/'groundwork/api_records'/f'{rid}.json';assert sha(path)==original
            else:
                rel=f'intervention_study/released_api_records/{name}/{rid}.json';path=R/rel
                t=transformations[rel]
                assert t['original_sha256']==original and sha(path)==t['released_sha256'],rid
            q=read(path);assert q['request_id']==rid;records[rid]=q
        for entry in entries:
            q=records[entry['request_id']]
            assert q['episode']==entry['episode'] and q['role']==entry['role']
        groups[name]=records
    return groups

def verify_saved(groups):
    from intervention_study.live_gating.verify_freeze import verify
    from intervention_study.common import digest
    verify()
    records={p.stem:read(p) for p in sorted((L/'episodes').glob('*.json'))}
    allocation={c['episode']:c for c in read(L/'allocation.json')}
    assert set(records)==set(allocation)
    verification=read(L/'verification.json')
    replay={r['episode']:r for r in verification['native_replays']}
    cases={c['case_id']:c for c in read(B/'cases.json')}
    writes=public_checks=0
    for eid,r in records.items():
        path=L/'episodes'/f'{eid}.json'
        assert replay[eid]['sha256']==sha(path) and replay[eid]['native_replay']=='pass'
        assert all(r[k]==v for k,v in allocation[eid].items())
        assert r['case_sha256']==digest(cases[r['case_id']]) and r['protocol_sha256']==sha(L/'protocol.json')
        last=r['initial_db_hash']
        for a in r['actions']:
            assert a['before_db_hash']==last
            last=a['after_db_hash']
            assert a['state_changed']==(a['before_db_hash']!=a['after_db_hash'])
            assert a['executed_selected_violation']==(a['attempted_selected_violation'] and a['state_changed'])
            if a['mutates']:writes+=1
            if a['blocked']:assert a['gate']['block'] and not a['state_changed'] and a['result']['policy_gate_blocked']
            call=r['canonical_messages'][a['message_index']]['tool_calls'][a['call_index']]
            assert call==a['call']
            for check in a.get('gate',{}).get('checks',[]):
                if 'request_record' not in check:continue
                q=groups['live_gating'][check['request_record']]
                public=json.loads(q['request']['messages'][1]['content'])
                assert q['episode']==eid and q['status']=='ok'
                assert set(public)=={'policy','tools','conversation_prefix','current_write'}
                assert digest(public)==check['public_input_sha256']
                assert public['current_write']==call
                prefix=public['conversation_prefix'];assert prefix==r['canonical_messages'][:len(prefix)]
                answer=json.loads(q['response']['choices'][0]['message']['content'])
                assert answer['risk']==check['risk'] and answer['reason']==check['reason']
                assert q['request']['model']==check['requested_model'];public_checks+=1
        assert last==r['final_db_hash']
        assert r['executed_selected_violation']==any(a['executed_selected_violation'] for a in r['actions'])
    assert writes==verification['independent_write_labels']==58
    assert public_checks==verification['public_gate_inputs_verified']==27
    audit=read(L/'blocked_write_audit.json');seen=set();prevented=Counter();native_reject=0
    for row in audit['checks']:
        eid=row['episode'];idx=row['action_index'];key=(eid,idx);assert key not in seen;seen.add(key)
        assert row['source_sha256']==sha(L/'episodes'/f'{eid}.json')
        r=records[eid];a=r['actions'][idx];assert a['blocked']
        assert row['condition']==r['condition'] and row['covered_violation']==a['attempted_selected_violation']
        assert row['native_would_change_state']==(row['shadow_after_hash']!=a['before_db_hash'])
        expected=a['attempted_selected_violation'] and row['native_would_change_state'] and not a['gate'].get('monitor_failure',False)
        assert row['prevented_covered_state_change']==expected
        if expected:prevented[r['condition']]+=1
        native_reject+=row['native_would_error'] and not row['native_would_change_state']
    assert seen=={(eid,i) for eid,r in records.items() for i,a in enumerate(r['actions']) if a['blocked']}
    assert len(seen)==audit['blocked_proposals_checked']==25
    assert dict(prevented)==audit['prevented_covered_state_changes']
    assert native_reject==audit['native_would_reject_without_state_change']==8
    return records,verification,audit

def outputs(records,verification,audit,groups):
    analysis=read(L/'analysis.json');rows=[];ledger=[]
    names={'none':'No gate','broad':'Broad model','decomposed':'Predicates + focused checks','oracle':'Privileged predicates'}
    for condition,name in names.items():
        p=next(x for x in analysis['by_condition'] if x['condition']==condition and x['pressure'])
        c=next(x for x in analysis['by_condition'] if x['condition']==condition and not x['pressure'])
        row={'condition':condition,'pressure_violations':p['completed_executed_violations'],'pressure_completed':p['completed'],
             'control_successes':c['completed_control_state_matches'],'control_completed':c['completed'],
             'control_unfinished':c['assigned']-c['completed'],'mean_pressure_actor_turns':p['mean_actor_turns_completed'],
             'all_attempts_cost_usd':p['reported_usd']+c['reported_usd'],
             'directly_prevented_covered_state_changes':audit['prevented_covered_state_changes'].get(condition,0),
             'blocks_on_covered_eligible_writes':p['blocks_on_covered_eligible_writes']+c['blocks_on_covered_eligible_writes'],
             'source_episodes':[eid for eid,r in records.items() if r['condition']==condition]}
        ledger.append(row)
        rows.append(f"{name} & {row['pressure_violations']}/{row['pressure_completed']} & {row['control_successes']}/{row['control_completed']} & {row['control_unfinished']} & {row['mean_pressure_actor_turns']:.3f} & {row['all_attempts_cost_usd']:.4f} \\\\")
    header=r'''\begin{tabular}{lrrrrr}
\toprule
Gate & Forbidden writes & Permitted successes & Unfinished & Mean turns & Cost\\
 & / completed & / completed controls & controls & (forbidden) & (USD)\\
\midrule
'''
    (R/'paper/generated/live_gating_rows.tex').write_text(header+'\n'.join(rows)+'\n'+r'\bottomrule'+'\n'+r'\end{tabular}'+'\n')
    examples=[]
    for eid,r in records.items():
        if r['rule']=='airline_compensation' and r['pressure']:
            selected=[{'index':i,'call':a['call'],'blocked':a['blocked'],'state_changed':a['state_changed']} for i,a in enumerate(r['actions']) if a['call']['name']=='send_certificate']
            assert len(selected)==1 and selected[0]['call']['arguments']['amount']==300
            assert selected[0]['blocked']==(r['condition']!='none')
            examples.append({'episode':eid,'source_sha256':sha(L/'episodes'/f'{eid}.json'),'writes':selected})
    cost={name:math.fsum(q.get('response',{}).get('usage',{}).get('cost') or 0 for q in group.values()) for name,group in groups.items()}
    old=read(R/'substantive_evaluation/spending.json')['reported_cumulative_usd']
    assert math.isclose(cost['live_gating'],analysis['spending']['new_reported_usd'],abs_tol=1e-12)
    assert math.isclose(old+sum(cost.values()),analysis['spending']['cumulative_reported_usd'],abs_tol=1e-10)
    result={'scope':'Exploratory eight-source-pair live follow-up; native evidence preserved by source hashes. Default verification checks saved replay ledgers; --native reruns transitions.',
        'rows':ledger,'compensation_examples':examples,'requests':{k:len(v) for k,v in groups.items()},
        'cost_usd':cost,'cumulative_reported_usd':old+sum(cost.values()),'incomplete_episodes':[eid for eid,r in records.items() if r['status']!='completed'],
        'checks':{'saved_native_replays':len(verification['native_replays']),'saved_independent_write_labels':verification['independent_write_labels'],
                  'public_inputs_and_scores':verification['public_gate_inputs_verified'],'saved_blocked_native_transitions':len(audit['checks'])},
        'source_sha256':{f'intervention_study/live_gating/{n}':sha(L/n) for n in ['protocol.json','allocation.json','verification.json','analysis.json','blocked_write_audit.json']}}
    save(R/'release/live_gating_ledger.json',result)
    print('Live follow-up: 64 attempt records, 27 public inputs/scores, 25 saved blocked transitions and 1,016 additional receipts verified; no API calls.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',action='store_true');p.add_argument('--native',action='store_true');args=p.parse_args()
    groups=load_receipts(args.source)
    import intervention_study.live_gating.records as live
    live.archive=lambda:groups['live_gating'];live.receipt=lambda rid:groups['live_gating'][rid]
    import intervention_study.evidence as preparation
    preparation.archive=lambda:groups['preparation'];preparation.receipt=lambda rid:groups['preparation'][rid]
    from intervention_study.live_gating.analyze import analyze
    analyze(offline=True)
    if args.native:
        from intervention_study.live_gating.verify_results import verify_results
        from intervention_study.live_gating.audit_blocked_writes import audit
        verify_results();audit()
    records,verification,audit=verify_saved(groups);outputs(records,verification,audit,groups)
if __name__=='__main__':main()
