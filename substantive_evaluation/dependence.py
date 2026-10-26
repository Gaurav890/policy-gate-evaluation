"""Additional entity-linked component sensitivity; fixed before score inspection."""
import json,statistics,collections
from pathlib import Path
from substantive_evaluation.analyze import uncertainty
B=Path(__file__).resolve().parent
def main():
 a=json.loads((B/'analysis.json').read_text());points=json.loads((B/'matched_points.json').read_text());mapping={t:i for i,ts in enumerate(a['task_components_linked_by_visible_user_order_or_reservation']) for t in ts};out=[]
 for cohort in ['substantive_audit/episodes','substantive_evaluation/episodes']:
  for model in ['gemini','gptmini']:
   for clean in [False,True]:
    bytask=collections.defaultdict(list)
    for r in points:
     if r['cohort']!=cohort or r['model']!=model or clean and (r['interaction_violation'] or r['policy_tool_discrepancy']) or any(x is None for x in r['risks'].values()):continue
     bytask[r['task']].append(int(r['risks']['broad']>=.5)-int(r['risks']['substantive']>=.5))
    components=collections.defaultdict(list)
    for t,vs in bytask.items():components[mapping[t]].append(statistics.mean(vs))
    result=uncertainty([statistics.mean(vs) for vs in components.values()]);result['n_entity_components']=result.pop('n_tasks');result['leave_one_component_out']=result.pop('leave_one_task_out');result['warning']='Descriptive component resampling; components inferred from observed shared entities, not proof of independent templates.'
    out.append({'cohort':cohort,'model':model,'subset':'interaction_clean_no_policy_tool_discrepancy' if clean else 'all','estimand':'Equal-weight visible-entity-component means of task-average broad minus substantive alerts',**result})
 (B/'entity_sensitivity.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
