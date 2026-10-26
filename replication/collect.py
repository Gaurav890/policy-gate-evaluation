"""Collect the fixed complete remaining-test allocation without outcome filtering."""
import argparse,copy,json,sys,time,hashlib
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from replication.common import *
from gateway_budget import GatewayError,BudgetExceeded
from study.run_confirmatory import load_selected_task,make_audit_environment
from benchmark_adapter import bridge_generate,grade_deterministic
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.orchestrator.orchestrator import Orchestrator
from study.analyze_confirmatory import contract_event
class ActorGateway:
 def __init__(self,g,reminder):self.g=g;self.reminder=reminder
 def complete(self,model,messages,**kwargs):
  if self.reminder and kwargs.get('role')=='actor':
   messages=copy.deepcopy(messages);assert messages[0]['role']=='system';messages[0]['content']+='\n\n'+self.reminder
  return self.g.complete(model,messages,**kwargs)
def run(row,condition,repeat,p,g):
 name=f"rep-{row['domain']}-{row['task_id']}-deepseek-{condition}-r{repeat}";dest=BASE/'episodes'/(name+'.json')
 if dest.exists():return
 task=load_selected_task(row['domain'],row['task_id'],p);env=make_audit_environment(row['domain'],False)
 agent=LLMAgent(tools=env.get_tools(),domain_policy=env.get_policy(),llm=p['actor'],llm_args={});user=UserSimulator(llm=p['customer'],instructions=str(task.user_scenario),tools=None,llm_args={})
 orch=Orchestrator(domain=row['domain'],agent=agent,user=user,environment=env,task=task,max_steps=p['max_steps'],max_errors=10,seed=None,timeout=p['max_seconds'],simulation_id=name)
 record={**row,'episode':name,'actor':p['actor'],'condition':condition,'repeat':repeat,'status':'started','policy':env.policy,'tools':[t.openai_schema for t in env.get_tools()],'name_map':{},'max_steps':p['max_steps'],'seed':None,'actor_reminder':p['reminder'] if condition=='reminder' else None}
 write_json(dest,record);start=time.monotonic()
 try:
  generate=bridge_generate(ActorGateway(g,record['actor_reminder']),name)
  with patch('tau2.agent.llm_agent.generate',generate),patch('tau2.user.user_simulator.generate',generate):sim=orch.run()
  canonical=env.canonical_messages(sim.messages);grade=grade_deterministic(row['domain'],task,canonical,sim.termination_reason.value)
  if grade['pending_components']==['NL_ASSERTION'] and not task.evaluation_criteria.nl_assertions:grade['native_success']=grade['deterministic_pass'];grade['pending_components']=[]
  record.update(status='completed',simulation=sim.model_dump(mode='json'),canonical_messages=[m.model_dump(mode='json') for m in canonical],grading=grade,live_db_hash=env.get_db_hash())
 except Exception as exc:
  record.update(status='incomplete',error_type=type(exc).__name__,partial_messages=[m.model_dump(mode='json') for m in orch.get_messages()]);raise
 finally:record['elapsed_s']=time.monotonic()-start;write_json(dest,record)
 print(json.dumps({'episode':name,'status':'completed','db_match':grade['environment'].get('db_check',{}).get('db_match'),'contract_violation':any(contract_event(m) for m in record['simulation']['messages']),'held_usd':g.budget.total_reserved()}),flush=True)
def main():
 a=argparse.ArgumentParser();a.add_argument('--prepare',action='store_true');a.add_argument('--live',action='store_true');a.add_argument('--shard',type=int,default=0);a.add_argument('--shards',type=int,default=4);args=a.parse_args()
 freeze('collection',SOURCES+['replication/collect.py','study/run_confirmatory.py'],create=args.prepare)
 if args.prepare:return
 assert args.live and 0<=args.shard<args.shards
 p=plan();g=gateway()
 # Interleave domains, then repeats/conditions, independent of outcomes.
 rows=sorted(p['tasks'],key=lambda r:hashlib.sha256(r['task_group'].encode()).hexdigest())
 for i,row in enumerate(rows):
  for repeat in p['repeats']:
   for condition in (p['conditions'] if (i+repeat)%2==0 else p['conditions'][::-1]):
    cell=f"{row['task_group']}:{condition}:{repeat}"
    if int(hashlib.sha256(cell.encode()).hexdigest(),16)%args.shards!=args.shard:continue
    try:run(row,condition,repeat,p,g)
    except GatewayError:print(json.dumps({'preserved_incomplete':cell}),flush=True)
if __name__=='__main__':main()
