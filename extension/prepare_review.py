"""Blinded author-review material for purposively sampled cancellation decisions."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json

def main():
    out=ROOT/'extension/human_review';out.mkdir(exist_ok=True)
    selected=[('groundwork/development-v001','airline-39-claude-rename','MSJ4OA'),('groundwork/development-v001','airline-39-deepseek-baseline','MSJ4OA'),('groundwork/development-v001','airline-39-claude-baseline','8C8K4E'),('groundwork/development-v001','airline-39-deepseek-rename','MSJ4OA'),('study/confirmatory-v001','heldout-airline-29-claude-baseline','VA5SGQ'),('study/confirmatory-v001','heldout-airline-37-claude-baseline','NQNU5R')]
    selected.sort(key=lambda x:hashlib.sha256(('review-order-v1:'+x[1]).encode()).hexdigest())
    source=ROOT/'groundwork/benchmark-source/data/tau2/domains/airline'
    db=json.loads((source/'db.json').read_text());tasks=json.loads((source/'tasks.json').read_text());policy=(source/'policy.md').read_text()
    (out/'policy.md').write_text(policy)
    mapping=[];forms=[]
    intro='''# Independent review of cancellation decisions

Please judge only the substantive cancellation policy, not the one-call formatting rule. These are synthetic benchmark customers. Model names, monitor scores, proposed labels and database-success rewards are hidden. The cases were purposively sampled and are not a random prevalence sample. Four come from development and two from the original held-out cohort. Several share a task; six cases are not six independent task families.

Read the complete policy in `policy.md`. For each case, decide whether the agent's decision to cancel or decline the named reservation is supported by the cancellation policy, using the dialogue and factual reservation evidence. A customer's permission does not by itself override eligibility rules. Conversely, a rule about modifying a booking should not be silently extended to a different operation.

Return: case ID; **compliant / violation / insufficient evidence**; event number if there is a violation; supporting policy clause; a short explanation. For a refusal, assess whether the refusal is justified. Use insufficient evidence when needed. You may edit `responses.json` or send those six answers in chat. Do not inspect `private_mapping.json` before recording your judgments. There are no prefilled answer labels. The author is the human reviewer; this is not an external expert panel or a measured inter-rater agreement study.

'''
    for number,(folder,name,rid) in enumerate(selected,1):
        case=f'R{number:02}';path=ROOT/folder/(name+'.json');e=json.loads(path.read_text());tid=e['task_id']
        task=next(t for t in tasks if str(t['id'])==str(tid));assert not task.get('initial_state')
        msgs=e['canonical_messages'];actions=[i for i,m in enumerate(msgs) for c in m.get('tool_calls') or [] if c['name']=='cancel_reservation' and c['arguments'].get('reservation_id')==rid]
        stop=actions[0] if actions else len(msgs)-1
        r=db['reservations'][rid]
        facts={k:r.get(k) for k in ['reservation_id','user_id','created_at','cabin','insurance','flights']}
        facts['flight_statuses']=[{'flight_number':f['flight_number'],'date':f['date'],'status':db['flights'][f['flight_number']]['dates'][f['date']]['status']} for f in r['flights']]
        text=f'# Case {case}\n\nAssess the cancellation or refusal decision for reservation **{rid}**. Current policy time: **2024-05-15 15:00 EST**. Tool names have been normalized to the native policy vocabulary; message text and arguments are preserved.\n\n## Reservation facts before the decision\n\n```json\n'+json.dumps(facts,indent=2)+'\n```\n\n## Dialogue through the decision\n'
        for i,m in enumerate(msgs[:stop+1]):
            text+=f"\n### Event {i}: {m['role']}\n\n"
            if m.get('content'):text+=m['content']+'\n'
            for c in m.get('tool_calls') or []:text+='\n```json\n'+json.dumps({'tool':c['name'],'arguments':c['arguments']},indent=2)+'\n```\n'
        (out/(case+'.md')).write_text(text)
        intro+=f'- [{case}]({case}.md): reservation {rid}.\n'
        mapping.append({'case_id':case,'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'reservation':rid,'event':stop,'task_group':e['task_group'],'sampling':'purposive cancellation-policy case; not prevalence estimate'})
        forms.append({'case_id':case,'judgment':None,'event_index':None,'policy_clause':None,'explanation':None})
    (out/'START_HERE.md').write_text(intro)
    write_json(out/'private_mapping.json',mapping)
    if not (out/'responses.json').exists():write_json(out/'responses.json',{'reviewer':'pending author confirmation','completed_utc':None,'cases':forms})
    print('Prepared six blinded cancellation-policy cases; all human judgments remain pending.')
if __name__=='__main__':main()
