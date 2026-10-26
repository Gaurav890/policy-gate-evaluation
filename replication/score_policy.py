"""Two declared monitor targets on identical controlled simulator prefixes."""
import argparse,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from replication.common import *
from replication.score import score_one
from replication.policy_lab import TARGET_PROMPT
from run_monitors import PROMPT
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--live',action='store_true');p.add_argument('--model',choices=['gemini','deepseek','gptmini']);a=p.parse_args()
 freeze('policy_monitor',SOURCES+['replication/score.py','replication/score_policy.py','replication/policy_lab.py','replication/policy_lab/cases.json'],create=a.prepare)
 if a.prepare:raise SystemExit(0)
 assert a.live and a.model;g=gateway()
 for i,row in enumerate(json.loads((BASE/'policy_lab/cases.json').read_text())):
  targets=['broad','eligibility'] if i%2==0 else ['eligibility','broad']
  for target in targets:
   out=BASE/'policy_lab/scores'/a.model/target/(row['case_id']+'.json')
   score_one(g,a.model,row['case_id'],len(row['public_input']['conversation_prefix'])-1,row['public_input'],out,role='replication_policy_'+target,prompt=PROMPT if target=='broad' else TARGET_PROMPT)
  print(json.dumps({'case':row['case_id'],'model':a.model,'held_usd':g.budget.total_reserved()}),flush=True)
