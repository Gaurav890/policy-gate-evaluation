"""Prospectively allocated repeated collection with unedited native proposals."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,write_json,GatewayError,BudgetExceeded
from gateway_v2 import Gateway
from budget_reconciled import Budget
from study.run_confirmatory import load_selected_task,make_audit_environment
from benchmark_adapter import bridge_generate,grade_deterministic
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.orchestrator.orchestrator import Orchestrator
from study.analyze_confirmatory import contract_event
CAP=26.54847889375

class ReminderGateway(Gateway):
    reminder=None
    def complete(self,model,messages,**kwargs):
        if self.reminder and kwargs.get('role')=='actor':
            messages=copy.deepcopy(messages)
            assert messages[0]['role']=='system' and isinstance(messages[0]['content'],str)
            messages[0]['content']+='\n\n'+self.reminder
        return super().complete(model,messages,**kwargs)

def run(row,condition,repeat,plan,gateway):
    name=f"ext-{row['domain']}-{row['task_id']}-deepseek-{condition}-r{repeat}"
    path=ROOT/'extension/episodes'/f'{name}.json'
    if path.exists():return
    gateway.reminder=plan['reminder'] if condition=='reminder' else None
    task=load_selected_task(row['domain'],row['task_id'],plan);env=make_audit_environment(row['domain'],False)
    agent=LLMAgent(tools=env.get_tools(),domain_policy=env.get_policy(),llm='deepseek',llm_args={})
    user=UserSimulator(llm='claude',instructions=str(task.user_scenario),tools=None,llm_args={})
    orch=Orchestrator(domain=row['domain'],agent=agent,user=user,environment=env,task=task,max_steps=90,max_errors=10,seed=None,timeout=900,simulation_id=name)
    record={**row,'episode':name,'actor':'deepseek','condition':condition,'repeat':repeat,'status':'started','policy':env.policy,'tools':[t.openai_schema for t in env.get_tools()],'name_map':{},'actor_reminder':gateway.reminder,'max_steps':90,'seed':None}
    write_json(path,record);start=time.monotonic()
    try:
        generate=bridge_generate(gateway,name)
        with patch('tau2.agent.llm_agent.generate',generate),patch('tau2.user.user_simulator.generate',generate):sim=orch.run()
        canonical=env.canonical_messages(sim.messages);grade=grade_deterministic(row['domain'],task,canonical,sim.termination_reason.value)
        if grade['pending_components']==['NL_ASSERTION'] and not task.evaluation_criteria.nl_assertions:
            grade['native_success']=grade['deterministic_pass'];grade['pending_components']=[]
        record.update(status='completed',simulation=sim.model_dump(mode='json'),canonical_messages=[m.model_dump(mode='json') for m in canonical],grading=grade,live_db_hash=env.get_db_hash())
    except Exception as exc:
        record.update(status='incomplete',error_type=type(exc).__name__,partial_messages=[m.model_dump(mode='json') for m in orch.get_messages()]);raise
    finally:
        record['elapsed_s']=time.monotonic()-start;write_json(path,record)
    print(json.dumps({'episode':name,'db_match':grade['environment'].get('db_check',{}).get('db_match'),'contract_violation':any(contract_event(m) for m in record['simulation']['messages']),'messages':len(sim.messages),'held_usd':gateway.budget.total_reserved()}),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--phase',choices=['feasibility','full'],required=True);p.add_argument('--domain',choices=['retail','airline']);a=p.parse_args()
    if not a.live:raise SystemExit('--live required')
    plan=json.loads((ROOT/'extension/plan.json').read_text())
    sources=['extension/collect.py','extension/plan.json','study/run_confirmatory.py','gateway_v2.py','budget_reconciled.py','benchmark_adapter.py']
    freeze={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources};fp=ROOT/'extension/collection_freeze.json'
    if fp.exists():assert json.loads(fp.read_text())==freeze
    else:write_json(fp,freeze)
    gateway=ReminderGateway(Budget(ceiling=CAP))
    rows=plan['tasks']
    if a.phase=='feasibility':
        rows=[next(r for r in rows if r['domain']==d) for d in ['retail','airline']]
        for r in rows:run(r,'reminder',0,plan,gateway)
    else:
        gate=json.loads((ROOT/'extension/feasibility.json').read_text());assert gate['expand_reminder']
        for i,r in enumerate(rows):
            if a.domain and r['domain']!=a.domain:continue
            for repeat in plan['repeats']:
                conditions=plan['conditions'] if (i+repeat)%2==0 else list(reversed(plan['conditions']))
                for condition in conditions:
                    try:run(r,condition,repeat,plan,gateway)
                    except GatewayError:print('Preserved incomplete cell',r['task_group'],condition,repeat,flush=True)
if __name__=='__main__':main()
