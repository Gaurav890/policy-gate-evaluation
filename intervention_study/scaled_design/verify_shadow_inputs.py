"""Check extraction on all historical ungated attempts, without monitor inference."""
from pathlib import Path
import json,hashlib
from intervention_study.common import BASE,read,digest,save
from intervention_study.scaled_design.shadow import export_record
HERE=Path(__file__).resolve().parent

def main():
 cases={c['case_id']:c for c in read(BASE/'cases.json')};records=[];rows=[]
 for path in sorted((BASE/'live_gating/episodes').glob('*--none--*.json')):
  record=read(path);out=export_record(record,cases[record['case_id']]);rows+=out
  records.append({'episode':record['episode'],'source_sha256':digest(path),'writes':len(out),'public_input_sha256':[r['public_sha256'] for r in out]})
 assert len(records)==16
 out={'source':'Historical 64-attempt exploratory cohort, 16 ungated attempts; engineering verification only.','new_paid_requests':0,'new_monitor_outputs':0,'source_records':records,'write_inputs':len(rows),
  'covered_violating_proposals':sum(r['covered_violation'] for r in rows),'covered_violating_state_changes':sum(r['covered_violation'] and r['native_state_change'] for r in rows),
  'native_rejected_covered_proposals':sum(r['covered_violation'] and r['native_error'] and not r['native_state_change'] for r in rows)}
 save(HERE/'shadow_input_check.json',out);print({k:v for k,v in out.items() if k!='source_records'})
if __name__=='__main__':main()
