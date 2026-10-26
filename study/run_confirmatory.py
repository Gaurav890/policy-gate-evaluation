"""Native held-out audit collection using frozen model and interface conditions."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json,GatewayError,BudgetExceeded
from gateway_v2 import Gateway
from budget_reconciled import Budget
from benchmark_adapter import make_environment,replace_names,bridge_generate,grade_deterministic
from prepare_manifest import build_manifest
from tau2.data_model.tasks import Task
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.orchestrator.orchestrator import Orchestrator


def load_selected_task(domain,tid,plan):
    if (domain,str(tid)) not in {(x['domain'],x['task_id']) for x in plan['tasks']}:raise ValueError('Not in frozen held-out selection')
    tasks=json.loads((ROOT/'groundwork/benchmark-source/data/tau2/domains'/domain/'tasks.json').read_text())
    return Task.model_validate(next(x for x in tasks if str(x['id'])==str(tid)))


def make_audit_environment(domain,shifted):
    env=make_environment(domain,False)
    if shifted:
        env.name_map={t.name:('service_'+t.name if t.name!='calculate' else t.name) for t in env.get_tools()}
        env.inverse={v:k for k,v in env.name_map.items()}
        env.policy=replace_names(env.policy,env.name_map)
    return env


def run(gateway,row,actor,condition,plan,out):
    name=f"heldout-{row['domain']}-{row['task_id']}-{actor}-{condition}"
    path=out/(name+'.json')
    if path.exists():return
    task=load_selected_task(row['domain'],row['task_id'],plan)
    env=make_audit_environment(row['domain'],condition=='rename')
    agent=LLMAgent(tools=env.get_tools(),domain_policy=env.get_policy(),llm=actor,llm_args={})
    user=UserSimulator(llm='claude',instructions=str(task.user_scenario),tools=None,llm_args={})
    orch=Orchestrator(domain=row['domain'],agent=agent,user=user,environment=env,task=task,max_steps=60,max_errors=10,seed=None,timeout=900,simulation_id=name)
    record={**row,'episode':name,'actor':actor,'condition':condition,'status':'started','policy':env.policy,
            'tools':[t.openai_schema for t in env.get_tools()],'name_map':env.name_map,'max_steps':60,'seed':None}
    write_json(path,record);start=time.monotonic()
    try:
        generate=bridge_generate(gateway,name)
        with patch('tau2.agent.llm_agent.generate',generate),patch('tau2.user.user_simulator.generate',generate):sim=orch.run()
        canonical=env.canonical_messages(sim.messages)
        grade=grade_deterministic(row['domain'],task,canonical,sim.termination_reason.value)
        if grade['pending_components']==['NL_ASSERTION'] and not task.evaluation_criteria.nl_assertions:
            grade['native_success']=grade['deterministic_pass'];grade['pending_components']=[]
            grade['empty_language_assertions_resolved']=True
        record.update(status='completed',simulation=sim.model_dump(mode='json'),canonical_messages=[m.model_dump(mode='json') for m in canonical],grading=grade,live_db_hash=env.get_db_hash())
    except Exception as exc:
        record.update(status='incomplete',error_type=type(exc).__name__,partial_messages=[m.model_dump(mode='json') for m in orch.get_messages()])
        write_json(path,record)
        raise
    finally:
        record['elapsed_s']=time.monotonic()-start;write_json(path,record)
    print(json.dumps({'episode':name,'status':record['status'],'db_match':grade['environment'].get('db_check',{}).get('db_match'),
                      'native_success':grade['native_success'],'termination':sim.termination_reason.value,'messages':len(sim.messages),
                      'budget_held_usd':round(gateway.budget.total_reserved(),4)}),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');args=p.parse_args()
    if not args.live:raise SystemExit('--live required')
    plan=json.loads((ROOT/'study/confirmatory_manifest.json').read_text())
    assert build_manifest(ROOT/'groundwork/benchmark-source')==json.loads((ROOT/'pilot_manifest.json').read_text())
    out=ROOT/'study/confirmatory-v001';out.mkdir(exist_ok=True)
    files=['study/run_confirmatory.py','study/confirmatory_manifest.json','gateway_v2.py','budget_reconciled.py','gateway_budget.py','benchmark_adapter.py','run_monitors.py']
    freeze={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    fpath=out/'freeze.json'
    if fpath.exists() and json.loads(fpath.read_text())!=freeze:raise SystemExit('Frozen code changed')
    write_json(fpath,freeze)
    gateway=Gateway(Budget(ceiling=22))
    for i,row in enumerate(plan['tasks']):
        actors=['claude','deepseek'] if i%2==0 else ['deepseek','claude']
        for actor in actors:
            conditions=['baseline','rename'] if (i+['claude','deepseek'].index(actor))%2==0 else ['rename','baseline']
            for condition in conditions:
                try:run(gateway,row,actor,condition,plan,out)
                except BudgetExceeded:
                    print(json.dumps({'status':'budget_stop','next_cell':[row['domain'],row['task_id'],actor,condition]}),flush=True);return
                except GatewayError:
                    print(json.dumps({'status':'infrastructure_interruption_preserved','cell':[row['domain'],row['task_id'],actor,condition]}),flush=True)

if __name__=='__main__':main()
