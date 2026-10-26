"""Frozen matched-input monitoring, with all failed outputs retained as missing."""
import argparse,hashlib,json,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from replication.common import *
from gateway_budget import GatewayError
from run_monitors import PROMPT,FORMAT,prefix_views

def score_one(g,model,episode,event,public,out,role='replication_monitor',prompt=PROMPT):
 h=hashlib.sha256(json.dumps(public,sort_keys=True).encode()).hexdigest()
 if out.exists():
  r=json.loads(out.read_text());assert r['public_input_sha256']==h;return r
 tag=f"{episode}--event-{event:03}";offset=g.budget.ledger.stat().st_size if g.budget.ledger.exists() else 0
 row={'episode':episode,'event_index':event,'model':model,'public_input_sha256':h}
 try:
  message,record=g.complete(model,[{'role':'system','content':prompt},{'role':'user','content':json.dumps(public,ensure_ascii=False)}],max_tokens=512,role=role+'_'+model,episode=tag,response_format=FORMAT)
  answer=json.loads(message['content']);risk=answer['risk']
  assert not isinstance(risk,bool) and isinstance(risk,(float,int)) and math.isfinite(risk) and 0<=risk<=1 and isinstance(answer['reason'],str)
  row.update(status='scored',risk=risk,reason=answer['reason'],request_record=record['request_id'])
 except (GatewayError,json.JSONDecodeError,AssertionError,KeyError,TypeError) as exc:
  with g.budget.ledger.open() as f:f.seek(offset);entries=[json.loads(l) for l in f if l.strip()]
  matches=[r['request_id'] for r in entries if r['episode']==tag and r['role']==role+'_'+model]
  row.update(status='missing',error_type=type(exc).__name__,attempt_records=matches)
 write_json(out,row);return row

def main():
 a=argparse.ArgumentParser();a.add_argument('--prepare',action='store_true');a.add_argument('--live',action='store_true');a.add_argument('--model',choices=['gemini','deepseek','gptmini']);a.add_argument('--cohort',choices=['original','extension','replication']);a.add_argument('--shard',type=int,default=0);a.add_argument('--shards',type=int,default=2);args=a.parse_args()
 freeze('monitor',SOURCES+['replication/score.py'],create=args.prepare)
 if args.prepare:return
 assert args.live and 0<=args.shard<args.shards
 if args.cohort!='replication':assert args.model=='gptmini'
 g=gateway();folder={'original':'study/confirmatory-v001','extension':'extension/episodes','replication':'replication/episodes'}[args.cohort]
 for path in sorted((ROOT/folder).glob('*.json')):
  if int(hashlib.sha256(path.name.encode()).hexdigest(),16)%args.shards!=args.shard:continue
  e=json.loads(path.read_text())
  if e.get('status')!='completed':continue
  out=BASE/'monitors'/args.cohort/args.model
  for v in prefix_views(e):score_one(g,args.model,e['episode'],v['event_index'],v['input'],out/f"{e['episode']}--event-{v['event_index']:03}.json")
  print(json.dumps({'scored':e['episode'],'model':args.model,'held_usd':g.budget.total_reserved()}),flush=True)
if __name__=='__main__':main()
