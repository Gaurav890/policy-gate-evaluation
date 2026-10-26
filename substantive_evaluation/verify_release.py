"""Check allocation, frozen sources, coverage, hashes and monitor schema."""
import json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
def verify():
    root=Path(__file__).resolve().parents[1]
    for name,h in json.loads((root/'substantive_evaluation/collection_freeze.json').read_text()).items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==h, name
    return json.loads((root/'substantive_evaluation/protocol.json').read_text())
from substantive_evaluation.monitor import verify as verify_monitor,windows
R=Path(__file__).resolve().parents[1];B=R/'substantive_evaluation';p=verify();cfg=verify_monitor()
for s,h in json.loads((B/'analysis_freeze.json').read_text()).items():assert hashlib.sha256((R/s).read_bytes()).hexdigest()==h,s
es=[json.loads(x.read_text()) for x in (B/'episodes').glob('*.json')];assert len(es)==96
assert {(e['task_group'],e['actor'],e['repeat']) for e in es}=={(c['task_group'],c['actor'],c['repeat']) for c in p['cells']}
assert all(e['status'] in ['completed','incomplete'] for e in es)
expected=[];missing=[];invalid=[]
for folder in cfg['cohorts']:
 for path in (R/folder).glob('*.json'):
  d=json.loads(path.read_text())
  if d['status']!='completed':continue
  for v in windows(d):
   h=hashlib.sha256(json.dumps(v['input'],sort_keys=True).encode()).hexdigest()
   assert set(v['input'])=={'policy','tools','conversation_prefix'}
   assert len(v['input']['conversation_prefix'])==v['event_index']+1
   for m in cfg['models']:
    for t in cfg['targets']:
     f=B/'scores'/m/t/f"{d['episode']}--event-{v['event_index']:03}.json";expected.append(f)
     if not f.exists():missing.append(str(f.relative_to(R)));continue
     s=json.loads(f.read_text());assert s['public_input_sha256']==h
     if s['status']!='scored':invalid.append(str(f.relative_to(R)))
     else:assert 0<=s['risk']<=1 and isinstance(s['reason'],str)
assert set(expected)==set((B/'scores').rglob('*.json'))|{R/x for x in missing}
labels=json.loads((B/'labels.json').read_text())
for l in labels:
 assert l['software_agreement']
 assert hashlib.sha256((R/l['source']).read_bytes()).hexdigest()==l['source_sha256']
 assert all(i<l['message_index'] for i in l['evidence_message_indices'])
a=json.loads((B/'analysis.json').read_text());assert a['expected_scores']==len(expected)
result={'planned_collection_cells':96,'collection_records':len(es),'completed_collection':sum(e['status']=='completed' for e in es),'expected_monitor_cells':len(expected),'unattempted_monitor_cells':missing,'preserved_invalid_monitor_cells':invalid,'frozen_sources':'pass','input_matching_and_public_whitelist':'pass','independent_software_labels':len(labels),'source_hashes':'pass','human_review_performed':False}
(B/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['unattempted_monitor_cells','preserved_invalid_monitor_cells']},indent=2));print('unattempted',len(missing),'preserved invalid',len(invalid));assert not missing
