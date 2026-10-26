"""Fixed exploratory pilot; preserve every attempt, including interruptions."""
import argparse, hashlib, json, sys, time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT, MODELS, write_json, GatewayError, BudgetExceeded
from gateway_v2 import Gateway
from budget_reconciled import Budget
from study.run_confirmatory import load_selected_task, make_audit_environment
from replication.collect import ActorGateway
from benchmark_adapter import bridge_generate, grade_deterministic
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.orchestrator.orchestrator import Orchestrator
BASE=ROOT/'substantive_audit'
def verify():
 f=json.loads((BASE/'pilot_freeze.json').read_text())
 for path,digest in f.items():
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest, 'Changed frozen input: '+path
 return json.loads((BASE/'pilot_protocol.json').read_text())
def run(row,actor,p,g):
 name=f"subpilot-{row['domain']}-{row['task_id']}-{actor}-r0"; dest=BASE/'episodes'/(name+'.json')
 if dest.exists(): return
 task=load_selected_task(row['domain'],row['task_id'],p);env=make_audit_environment(row['domain'],False)
 agent=LLMAgent(tools=env.get_tools(),domain_policy=env.get_policy(),llm=actor,llm_args={})
 user=UserSimulator(llm=p['customer'],instructions=str(task.user_scenario),tools=None,llm_args={})
 orch=Orchestrator(domain=row['domain'],agent=agent,user=user,environment=env,task=task,max_steps=p['max_steps'],max_errors=10,seed=None,timeout=p['max_seconds'],simulation_id=name)
 record={**row,'episode':name,'actor':actor,'condition':'interaction_reminder','repeat':0,'status':'started','policy':env.policy,'tools':[t.openai_schema for t in env.get_tools()],'name_map':{},'max_steps':p['max_steps'],'seed':None,'actor_reminder':p['reminder'],'protocol_sha256':hashlib.sha256((BASE/'pilot_protocol.json').read_bytes()).hexdigest()}
 write_json(dest,record);start=time.monotonic()
 try:
  generate=bridge_generate(ActorGateway(g,p['reminder']),name)
  with patch('tau2.agent.llm_agent.generate',generate),patch('tau2.user.user_simulator.generate',generate):sim=orch.run()
  canonical=env.canonical_messages(sim.messages);grade=grade_deterministic(row['domain'],task,canonical,sim.termination_reason.value)
  if grade['pending_components']==['NL_ASSERTION'] and not task.evaluation_criteria.nl_assertions:
   grade['native_success']=grade['deterministic_pass'];grade['pending_components']=[]
  record.update(status='completed',simulation=sim.model_dump(mode='json'),canonical_messages=[m.model_dump(mode='json') for m in canonical],grading=grade,live_db_hash=env.get_db_hash())
 except Exception as exc:
  record.update(status='incomplete',error_type=type(exc).__name__,partial_messages=[m.model_dump(mode='json') for m in orch.get_messages()]);raise
 finally:
  record['elapsed_s']=time.monotonic()-start;write_json(dest,record)
 print(json.dumps({'episode':name,'status':record['status'],'messages':len(canonical),'held_usd':g.budget.total_reserved()}),flush=True)
def main():
 a=argparse.ArgumentParser();a.add_argument('--live',action='store_true');a.add_argument('--shard',type=int,default=0);a.add_argument('--shards',type=int,default=4);args=a.parse_args()
 p=verify(); assert args.live and 0<=args.shard<args.shards
 MODELS.update(p['models']);g=Gateway(Budget(ceiling=p['pilot_cumulative_admission_ceiling_usd']))
 for i,cell in enumerate(p['cells']):
  if i%args.shards!=args.shard:continue
  row=next(r for r in p['tasks'] if r['task_group']==cell['task_group'])
  try:run(row,cell['actor'],p,g)
  except BudgetExceeded: print(json.dumps({'budget_stop':cell}),flush=True);return
  except GatewayError: print(json.dumps({'incomplete_preserved':cell}),flush=True)
if __name__=='__main__':main()
