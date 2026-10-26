"""Recount matched binary differences without imputing missing outcomes or fitting tests."""
import argparse, csv, hashlib, io, json
from collections import defaultdict
from pathlib import Path
from statistics import mean
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]

def value(record, outcome):
    bounded=record['status']=='completed' or record.get('termination') in ('actor_turn_limit','customer_turn_limit')
    if outcome=='executed_violation':
        positive=record.get('executed_selected_violation') or any(x.get('executed_selected_violation') for x in record.get('actions',[]))
        return 1 if positive else 0 if bounded else None
    return int(record['status']=='completed' and bool(record['control_reference_state_match'])) if bounded else None

def weighted_mean(cells, key):
    by_rule=defaultdict(lambda:defaultdict(list))
    for c in cells: by_rule[c['rule']][c['pair_id']].append(c[key])
    return mean(mean(mean(values) for values in pairs.values()) for pairs in by_rule.values())

def produce(root=ROOT):
    base=root/'intervention_study/compact_study'
    allocation=json.loads((base/'allocation.json').read_text())
    paths=sorted((base/'episodes').glob('*.json'))
    records=[json.loads(x.read_text()) for x in paths]
    assert len(records)==len(allocation)==1152
    assert {x['episode'] for x in records}=={x['episode'] for x in allocation}
    index={(x['pair_id'],x['actor'],x['repeat'],x['pressure'],x['condition']):x for x in records}
    assert len(index)==1152
    rows=[]
    for pressure,outcome in [(True,'executed_violation'),(False,'service_complete')]:
      for gate in ['broad','decomposed']:
        groups=defaultdict(list)
        for r in records:
          if r['condition']!=gate or r['pressure']!=pressure: continue
          b=index[(r['pair_id'],r['actor'],r['repeat'],pressure,'none')]
          g,n=value(r,outcome),value(b,outcome)
          c=dict(pair_id=r['pair_id'],rule=r['rule'],actor=r['actor'],gate_missing=int(g is None),base_missing=int(n is None),missing=int(g is None or n is None),lower=(0 if g is None else g)-(1 if n is None else n),upper=(1 if g is None else g)-(0 if n is None else n))
          for kind,group in [('overall','all'),('actor',r['actor']),('rule',r['rule']),('scenario',r['pair_id']),('scenario_actor',r['pair_id']+'/'+r['actor'])]: groups[(kind,group)].append(c)
        for (kind,group),cells in sorted(groups.items()):
          lo,hi=weighted_mean(cells,'lower'),weighted_mean(cells,'upper')
          missing=sum(c['missing'] for c in cells)
          rows.append(dict(level=kind,group=group,gate=gate,outcome=outcome,pressure=pressure,assigned_matched_cells=len(cells),scenario_pairs=len({c['pair_id'] for c in cells}),missing_matched_cells=missing,missing_gate=sum(c['gate_missing'] for c in cells),missing_ungated=sum(c['base_missing'] for c in cells),estimate=None if missing else lo,lower=lo,upper=hi))
    frozen=json.loads((root/'paper/combined_study/results_tables.json').read_text())
    for f in frozen['primary_contrasts']:
      row=next(x for x in rows if x['level']=='overall' and x['gate']==f['gate'] and x['outcome']==f['outcome'])
      assert all(abs(a-b)<1e-12 for a,b in zip([row['lower'],row['upper']],f['assignment_bounds']))
    result={'status':'post_hoc_descriptive_export','inference':'No p values or confidence intervals. Bounds cover missing binary values in these assignments only; all four frozen formal comparisons remain withheld.','matching':'scenario, actor, repeat and request type; gate minus ungated','weighting':'Mean across matched actor/repeat cells within pair, pairs within rule, then rules; within a subgroup use its retained cells.','episode_sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in paths},'rows':rows}
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    return {'paired_effects.json':json.dumps(result,indent=2,sort_keys=True)+'\n','paired_effects.csv':out.getvalue()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    outputs=produce()
    for name,text in outputs.items():
      path=HERE/name
      if args.check: assert path.read_text()==text,name
      else: path.write_text(text)
    print(json.dumps({'paired_export_verified':True,'rows':len(json.loads(outputs['paired_effects.json'])['rows']),'check_only':args.check,'model_calls':0}))
if __name__=='__main__':main()
