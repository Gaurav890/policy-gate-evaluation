"""Expose entity and coarse reference-sequence overlap with all earlier cohorts."""
import json,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'substantive_evaluation'
def read(folder):
 out=[]
 for p in (R/folder).glob('*.json'):
  d=json.loads(p.read_text())
  if 'episode' not in d:continue
  entities=set()
  for m in d.get('canonical_messages',d.get('partial_messages',[])):
   if m['role']!='tool':continue
   try:o=json.loads(m.get('content'))
   except (ValueError,TypeError):continue
   if not isinstance(o,dict):continue
   for k in ['user_id','order_id','reservation_id']:
    if o.get(k):entities.add(d['domain']+':'+k+':'+o[k])
  seq=d.get('reference_operation_sequence')
  out.append({'episode':d['episode'],'task':d['domain']+':'+str(d['task_id']),'entities':entities,'sequence':(d['domain'],tuple(seq)) if seq is not None else None})
 return out
def main():
 prior=[]
 for f in ['study/confirmatory-v001','extension/episodes','replication/episodes','substantive_audit/episodes','groundwork/development-v001','groundwork/recovery-v001']:prior+=read(f)
 new=read('substantive_evaluation/episodes');seen_entities=set().union(*(r['entities'] for r in prior));seen_tasks={r['task'] for r in prior};seen_sequences={r['sequence'] for r in prior if r['sequence'] is not None};bytask=collections.defaultdict(set)
 for r in new:bytask[r['task']]|=r['entities']
 out={'new_task_ids':len(bytask),'task_id_overlap_with_prior':sorted(set(bytask)&seen_tasks),'new_tasks_with_visible_entity_overlap':sum(bool(ids&seen_entities) for ids in bytask.values()),'unique_new_visible_entities':len(set().union(*bytask.values())) if bytask else 0,'task_details':[{'task':t,'visible_entities':len(ids),'shared_with_prior':len(ids&seen_entities)} for t,ids in sorted(bytask.items())],'new_reference_sequence_groups':len({r['sequence'] for r in new if r['sequence'] is not None}),'new_tasks_with_prior_reference_sequence':len({r['task'] for r in new if r['sequence'] in seen_sequences}),'warning':'Exact reference-operation sequence is a coarse grouping, not a semantic template oracle. Observed entity overlap is a lower bound because unqueried entities remain unobserved.'}
 (B/'dependency_inventory.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
