"""Supplemental descriptive strata and repeat consistency; no hypothesis tests."""
import json,collections,statistics
from pathlib import Path
B=Path(__file__).resolve().parent
p=json.loads((B/'matched_points.json').read_text());es=json.loads((B/'episode_results.json').read_text());out=[]
for model in ['gemini','gptmini']:
 for actor in ['deepseek','gptmini']:
  for domain in ['airline','retail']:
   for clean in [False,True]:
    rows=[r for r in p if r['cohort']=='substantive_evaluation/episodes' and r['model']==model and r['actor']==actor and r['domain']==domain and (not clean or not r['interaction_violation'] and not r['policy_tool_discrepancy']) and all(x is not None for x in r['risks'].values())]
    groups=collections.defaultdict(list)
    for r in rows:groups[r['task']].append(int(r['risks']['broad']>=.5)-int(r['risks']['substantive']>=.5))
    out.append({'model':model,'actor':actor,'domain':domain,'strict_subset':clean,'matched_prefixes':len(rows),'tasks':len(groups),'task_mean_broad_minus_substantive':statistics.mean(statistics.mean(v) for v in groups.values()) if groups else None})
pairs=collections.defaultdict(dict)
for e in es:
 if e['cohort']=='substantive_evaluation/episodes':pairs[(e['task'],e['actor'])][e['repeat']]=e
repeat=[]
for (task,actor),runs in pairs.items():
 if set(runs)!={0,1} or any(e['status']!='completed' for e in runs.values()):continue
 repeat.append({'task':task,'actor':actor,'selected_labels':[runs[i]['selected_rule_label'] for i in [0,1]],'selected_label_disagreement':runs[0]['selected_rule_label']!=runs[1]['selected_rule_label'],'interaction_disagreement':runs[0]['interaction_violation']!=runs[1]['interaction_violation'],'state_match_disagreement':runs[0]['db_match']!=runs[1]['db_match']})
(B/'strata.json').write_text(json.dumps({'scope':'Supplemental descriptive breakdown; not a preregistered confirmatory test.','target_comparisons':out,'repeat_pairs':repeat},indent=2)+'\n')
