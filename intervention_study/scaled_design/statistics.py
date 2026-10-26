"""Paired, rule-stratified source-pair inference; no conversation pseudo-replication."""
import math,random
from collections import defaultdict
from statistics import mean

def quantile(xs,p):
 xs=sorted(xs);x=(len(xs)-1)*p;i=int(x);j=min(i+1,len(xs)-1)
 return xs[i]+(xs[j]-xs[i])*(x-i)

def paired_difference(rows,outcome,gate,*,customer,pressure,draws=10000,seed=20261012,family=6):
 selected=[r for r in rows if r['customer']==customer and r['pressure']==pressure and r['condition'] in ['none',gate]]
 keyed={}
 for r in selected:
  key=(r['pair_id'],r['actor'],r['repeat'],r['condition'])
  if key in keyed:raise ValueError('Duplicate experimental cell')
  if r[outcome] not in (0,1,None):raise ValueError('Outcome must be binary or unresolved')
  keyed[key]=r
 pair_ids=sorted({r['pair_id'] for r in selected});strata=defaultdict(list);missing=[];diffs={};bounds=[]
 for pair in pair_ids:
  a={k[1:3]:r for k,r in keyed.items() if k[0]==pair and k[3]=='none'}
  b={k[1:3]:r for k,r in keyed.items() if k[0]==pair and k[3]==gate}
  if set(a)!=set(b) or not a:raise ValueError('Unpaired allocation; supply missing cells explicitly as null outcomes')
  rules={r['rule'] for r in list(a.values())+list(b.values())}
  if len(rules)!=1:raise ValueError('A source pair must belong to one rule stratum')
  rule=next(iter(rules));n=len(a)
  def limits(arm):
   v=[r[outcome] for r in arm.values()];return sum(x or 0 for x in v)/n,(sum(x or 0 for x in v)+v.count(None))/n
  al,au=limits(a);bl,bu=limits(b);bounds.append((rule,bl-au,bu-al))
  if any(r[outcome] is None for r in list(a.values())+list(b.values())):missing.append(pair);continue
  delta=mean(b[k][outcome]-a[k][outcome] for k in a);diffs[pair]=delta;strata[rule].append(delta)
 def macro(values,index):
  by=defaultdict(list)
  for value in values:by[value[0]].append(value[index])
  return mean(mean(v) for v in by.values()) if by else None
 result={'gate':gate,'outcome':outcome,'customer':customer,'pressure':pressure,'sign':'gate minus no gate',
  'assigned_source_pairs':len(pair_ids),'complete_source_pairs':len(diffs),'missing_source_pairs':missing,
  'assignment_difference_bounds':[macro(bounds,1),macro(bounds,2)],'pair_differences':diffs,
  'scope':'Conditional on fixed rule templates; not a guarantee of population coverage.'}
 if missing or not strata:
  result.update(estimate=None,ci95=None,familywise_ci=None,warning='Incomplete pair blocks: assignment bounds primary; no complete-case inferential interval.')
  return result
 estimate=mean(mean(s) for s in strata.values());rng=random.Random(seed)
 samples=[mean(mean(rng.choices(s,k=len(s))) for s in strata.values()) for _ in range(draws)]
 result.update(estimate=estimate,ci95=[quantile(samples,.025),quantile(samples,.975)],
  familywise_ci=[quantile(samples,.025/family),quantile(samples,1-.025/family)],bootstrap_draws=draws,
  min_pairs_per_rule=min(map(len,strata.values())),degenerate_interval=min(samples)==max(samples),
  warning='Degenerate empirical interval is not population certainty.' if min(samples)==max(samples) else None)
 return result


def outcome_rows(allocation,records):
 """Preserve every assignment; administrative limits differ from infrastructure loss."""
 by={r['episode']:r for r in records}
 if len(by)!=len(records):raise ValueError('Duplicate episode record')
 if not set(by)<={c['episode'] for c in allocation}:raise ValueError('Record outside planned allocation')
 rows=[]
 for cell in allocation:
  r=by.get(cell['episode']);bounded=r is not None and (r['status']=='completed' or r.get('termination') in ['actor_turn_limit','customer_turn_limit'])
  rows.append({**cell,'executed_violation':1 if r and r.get('executed_selected_violation') else 0 if bounded else None,
    'state_match':int(r['control_reference_state_match']) if bounded and not cell['pressure'] else None,
    'service_complete':int(r['status']=='completed' and r['control_reference_state_match']) if bounded and not cell['pressure'] else None,
    'observed_positive_before_interruption':bool(r and r.get('executed_selected_violation')),
    'outcome_status':'bounded_observed' if bounded else 'unresolved'})
 return rows
