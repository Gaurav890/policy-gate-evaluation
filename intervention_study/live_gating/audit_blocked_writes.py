"""Exploratory one-step native counterfactuals for every blocked proposal."""
import copy
from collections import Counter
from intervention_study.common import BASE,read,save,digest,environment
from intervention_study.serialization import to_json
RUNBASE=BASE/'live_gating'

def audit():
    cases={c['case_id']:c for c in read(BASE/'cases.json')};checks=[]
    for path in sorted((RUNBASE/'episodes').glob('*.json')):
        r=read(path);case=cases[r['case_id']];env=environment(case)
        for index,event in enumerate(r['actions']):
            assert env.get_db_hash()==event['before_db_hash']
            call=event['call']
            if event['blocked']:
                shadow=copy.deepcopy(env);error=False
                try:result=to_json(shadow.make_tool_call(call['name'],**call['arguments']))
                except (ValueError,TypeError,KeyError) as exc:result={'error':str(exc)};error=True
                changed=shadow.get_db_hash()!=event['before_db_hash']
                checks.append({'episode':r['episode'],'condition':r['condition'],'rule':r['rule'],'pressure':r['pressure'],
                    'action_index':index,'source_sha256':digest(path),'covered_violation':event['attempted_selected_violation'],
                    'monitor_failure':event['gate'].get('monitor_failure',False),'native_would_change_state':changed,
                    'native_would_error':error,'shadow_result':result,'shadow_after_hash':shadow.get_db_hash(),
                    'prevented_covered_state_change':event['attempted_selected_violation'] and changed and not event['gate'].get('monitor_failure',False)})
                assert env.get_db_hash()==event['before_db_hash']
            else:
                try:env.make_tool_call(call['name'],**call['arguments'])
                except (ValueError,TypeError,KeyError):pass
            assert env.get_db_hash()==event['after_db_hash']
    out={'scope':'Exploratory diagnostic added after collection began, separate from frozen primary outcomes. Execute each blocked proposal once on a private copy of its exact preceding native state. This is a one-step tool transition, not an alternative future conversation.',
        'blocked_proposals_checked':len(checks),'prevented_covered_state_changes':dict(Counter(r['condition'] for r in checks if r['prevented_covered_state_change'])),
        'native_would_reject_without_state_change':sum(r['native_would_error'] and not r['native_would_change_state'] for r in checks),'checks':checks}
    save(RUNBASE/'blocked_write_audit.json',out)
    print({k:v for k,v in out.items() if k!='checks'})

if __name__=='__main__':audit()
