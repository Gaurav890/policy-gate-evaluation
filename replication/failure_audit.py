"""Distinguish transport interruptions from complete simulator outcomes."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json
if __name__=='__main__':
 paths=list((ROOT/'replication/episodes').glob('*.json'));episodes=[json.loads(p.read_text()) for p in paths];failed={e['episode']:e for e in episodes if e['status']=='incomplete'};records=defaultdict(list)
 for p in (ROOT/'groundwork/api_records').glob('*.json'):
  r=json.loads(p.read_text())
  if r.get('episode') in failed:records[r['episode']].append(r)
 rows=[]
 for ep,e in sorted(failed.items()):
  rs=sorted(records[ep],key=lambda r:r['utc']);last=rs[-1] if rs else {};finish=[c.get('finish_reason') for c in last.get('response',{}).get('choices',[])]
  kind='output_truncation' if 'length' in finish else 'rate_limit' if last.get('http_status')==429 else 'timeout' if last.get('error_type')=='TimeoutError' else last.get('error_type',e.get('error_type'))
  rows.append({'episode':ep,'category':kind,'collector_error':e.get('error_type'),'last_request_id':last.get('request_id'),'last_role':last.get('role'),'partial_messages':len(e.get('partial_messages',[])),'failed_request_ids':[r['request_id'] for r in rs if r['status']=='request_failed']})
 out={'status_counts':dict(Counter(e['status'] for e in episodes)),'categories':dict(Counter(r['category'] for r in rows)),'rows':rows,'treatment':'Retain every attempted cell. Interrupted cells excluded from completed-conversation metrics, explicitly counted; no replacement or assumption that missingness is random.'}
 missing=[]
 for path in sorted((ROOT/'replication/monitors').rglob('*.json')):
  score=json.loads(path.read_text())
  if score['status']!='missing':continue
  ids=score['attempt_records'];last=json.loads((ROOT/'groundwork/api_records'/(ids[-1]+'.json')).read_text()) if ids else {}
  finish=[c.get('finish_reason') for c in last.get('response',{}).get('choices',[])]
  category='output_truncation' if 'length' in finish else 'rate_limit' if last.get('http_status')==429 else 'timeout' if last.get('error_type')=='TimeoutError' else 'invalid_structured_output' if last.get('status')=='ok' else last.get('error_type',score.get('error_type'))
  missing.append({'score_file':str(path.relative_to(ROOT)),'model':score['model'],'category':category,'attempt_records':ids})
 out['new_monitor_missing']={'count':len(missing),'categories':dict(Counter(r['category'] for r in missing)),'rows':missing}
 write_json(ROOT/'replication/failure_audit.json',out)
 print(json.dumps({'status':out['status_counts'],'interruptions':out['categories'],'new_monitor_missing':out['new_monitor_missing']['categories']}))
