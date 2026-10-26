"""Isolated airline collection worker; assigned cells are skipped by the original collector."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from study.run_confirmatory import *
def run(gateway,row,actor,condition,plan,out):
    name=f"heldout-{row['domain']}-{row['task_id']}-{actor}-{condition}"
    path=out/(name+'.json')
    if path.exists() and json.loads(path.read_text()).get('status') != 'assigned':return
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

if __name__=='__main__':
    plan=json.loads((ROOT/'study/confirmatory_manifest.json').read_text())
    out=ROOT/'study/confirmatory-v001'
    gateway=Gateway(Budget(ceiling=22))
    for i,row in enumerate(plan['tasks']):
        if row['domain']!='airline':continue
        actors=['claude','deepseek'] if i%2==0 else ['deepseek','claude']
        for actor in actors:
            conditions=['baseline','rename'] if (i+['claude','deepseek'].index(actor))%2==0 else ['rename','baseline']
            for condition in conditions:
                try:run(gateway,row,actor,condition,plan,out)
                except BudgetExceeded:raise SystemExit('Budget ceiling reached; assigned but unstarted cells remain visible')
                except GatewayError:print(json.dumps({'status':'infrastructure_interruption_preserved','cell':[row['domain'],row['task_id'],actor,condition]}),flush=True)
