"""Freeze a low-cost breadth screen within the same cumulative authorization."""
from intervention_study.common import BASE,ROOT,read,save,digest
from intervention_study.verify_v3 import verify_v3

def main():
    cfg=verify_v3();assert not (BASE/'freeze_breadth.json').exists()
    cfg['scope']='Development screen of all six rules absent from the 32-conversation recovery pilot, two reference actors, one pressure and one control per rule, no gate.'
    cfg['purpose']='Check task/controller feasibility across all eight rules before recommending the expensive full evaluation. Not a selected set of favorable failures.'
    cfg['pilot_cumulative_ceiling_usd']=95
    cells=[{**c,'episode':c['episode'].replace('intervention-','intervention-breadth-',1)} for c in read(BASE/'pilot_allocation.json') if c['rule'] not in cfg['recovery_rules'] and c['actor'] in ['deepseek_ref','gptmini_ref'] and c['condition']=='none']
    assert len(cells)==24
    save(BASE/'protocol_breadth.json',cfg);save(BASE/'pilot_allocation_breadth.json',cells)
    names=['runner_breadth.py','verify_breadth.py','prepare_breadth.py','protocol_breadth.json','pilot_allocation_breadth.json']
    save(BASE/'freeze_breadth.json',{'parent_freeze_sha256':digest(BASE/'freeze_v3.json'),'phase':'After 32 recovery conversations and 96 fixture checks; before breadth-screen calls','files':{str((BASE/n).relative_to(ROOT)):digest(BASE/n) for n in names}})
    print('Frozen 24 low-cost development screening cells, with the $95 admission ceiling unchanged.')
if __name__=='__main__':main()
