"""Explicit one-time continuation after a nested native-result serialization error."""
from intervention_study.common import BASE,ROOT,read,save,digest
from intervention_study.verify_breadth import verify_breadth
from intervention_study import runner_breadth as runner
from intervention_study.serialization import to_json
from intervention_study.runtime_guarded_v3 import gateway,STOP
from gateway_budget import BudgetExceeded

def main():
    cfg=verify_breadth();path=BASE/'serialization_amendment.json'
    names=['serialization.py','continue_breadth.py']
    if not path.exists():
        cells=[];interruptions=[]
        for cell in read(BASE/'pilot_allocation_breadth.json'):
            existing=BASE/'pilot_breadth'/(cell['episode']+'.json')
            if existing.exists() and read(existing)['status']=='completed':continue
            selected=dict(cell)
            if existing.exists():
                interruptions.append({'episode':cell['episode'],'source_sha256':digest(existing),'last_saved_status':read(existing)['status'],'resolved_status':'interrupted','reason':'Native list contained model objects that the original JSON adapter did not recursively convert.'})
                selected.update(original_episode=cell['episode'],episode=cell['episode']+'--serialization-retry-1')
            cells.append(selected)
        save(path,{'reason':'Data-format compatibility correction; no prompt, task, label or gate changes','files':{str((BASE/n).relative_to(ROOT)):digest(BASE/n) for n in names},'interruptions':interruptions,'continuation_cells':cells})
    amendment=read(path)
    for name,expected in amendment['files'].items():assert digest(ROOT/name)==expected
    runner.serial=to_json
    g=gateway(cfg['pilot_cumulative_ceiling_usd'])
    for cell in amendment['continuation_cells']:
        if STOP.exists():break
        try:runner.run({**cell,'runtime_amendment_sha256':digest(path)},cfg,g)
        except BudgetExceeded:break
if __name__=='__main__':main()
