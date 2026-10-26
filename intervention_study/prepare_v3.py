"""Freeze a turn-controller correction before collecting replacement development data."""
from intervention_study.common import BASE,ROOT,read,save,digest
from intervention_study.verify_v2 import verify_v2

def main():
    cfg=verify_v2();assert not (BASE/'freeze_v3.json').exists()
    cfg.update(version=3,customer_model=None,customer_controller='fixed_customer_v1',
      amendment_v3={'reason':'The model-generated customer mislabeled repeated pushbacks; an early circuit-breaker also remained open after a transient 429 retried successfully.',
      'changes':['Replace generated customer text/flags with a deterministic, visible-text turn controller and fixed known facts','At most two explicitly generated pressure replies, exact control confirmations, and separately recorded stop events','A returned completion phrase controls turn taking only; database-state success remains independently measured','Stop all workers only after the existing bounded transport retries fail or connection preflight fails','Same 32 planned case/actor/gate cells; v1 and v2 diagnostics retained, no silent replacements'],
      'scope':'Agents generate their responses and tool choices against scripted simulated customers. These are designed stress tests, not natural customer conversations or natural violation prevalence.'})
    cells=[{**c,'episode':c['episode'].replace('intervention-v2-','intervention-v3-',1)} for c in read(BASE/'pilot_allocation_v2.json')]
    save(BASE/'protocol_v3.json',cfg);save(BASE/'pilot_allocation_v3.json',cells)
    names=['customer_controller.py','runtime_guarded_v3.py','runner_v3.py','verify_v3.py','prepare_v3.py','protocol_v3.json','pilot_allocation_v3.json']
    save(BASE/'freeze_v3.json',{'parent_freeze_sha256':digest(BASE/'freeze_v2.json'),'phase':'After v2 engineering diagnostics; before any v3 inference','files':{str((BASE/n).relative_to(ROOT)):digest(BASE/n) for n in names}})
    print('Frozen fixed-customer recovery design: 32 conversations.')
if __name__=='__main__':main()
