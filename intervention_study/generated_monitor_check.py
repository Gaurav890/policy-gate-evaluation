"""Case-series monitoring of every executed violation found in the breadth pilot."""
import argparse,json,itertools
from intervention_study.common import BASE,read,save,digest,environment
from intervention_study.verify_breadth import verify_breadth
from intervention_study.gates import score,BROAD
from intervention_study.fixture_runner import SUBSTANTIVE
from intervention_study.predicates import check,observed_facts,public_context
from intervention_study.runtime_guarded_v3 import gateway,STOP
from gateway_budget import BudgetExceeded

def prepare():
    cfg=verify_breadth();path=BASE/'generated_monitor_manifest.json'
    if path.exists():return read(path)
    rows=[]
    for p in sorted((BASE/'pilot_breadth').glob('*.json')):
        episode=read(p)
        if not episode.get('executed_selected_violation'):continue
        case=next(c for c in read(BASE/'cases.json') if c['case_id']==episode['case_id']);env=environment(case)
        for i,event in enumerate(episode['actions']):
            if not event['executed_selected_violation']:continue
            prefix=episode['canonical_messages'][:event['message_index']+1+event['call_index']]
            public={'policy':env.policy,'tools':[t.openai_schema for t in env.get_tools()],'conversation_prefix':prefix,'current_write':event['call']}
            rows.append({'example_id':episode['episode']+'--write-'+str(i),'source':str(p.relative_to(BASE)),'source_sha256':digest(p),'action_index':i,'rule':case['rule'],
                         'public_input':public,'public_input_sha256':digest(public),'public_predicate_checks':check(case['domain'],event['call'],observed_facts(prefix),public_context(prefix))})
    assert len(rows)==3,'Review a changed case-series allocation before any calls.'
    manifest={'scope':'All three generated, executed violation examples from the breadth pilot. Selected positives only; not sensitivity, specificity, transfer, or a prevalence estimate.',
              'ceiling_usd':100,'selection':'Exhaustive executed positives after the breadth screen, with no exclusions based on monitor predictions.',
              'runner_sha256':digest(BASE/'generated_monitor_check.py'),'examples':rows,'models':cfg['fixture_monitors'],'targets':cfg['fixture_targets'],'planned_scores':36}
    save(path,manifest);return manifest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--live',action='store_true');parser.add_argument('--shard',type=int,default=0);parser.add_argument('--shards',type=int,default=1);args=parser.parse_args()
    manifest=prepare();assert digest(BASE/'generated_monitor_check.py')==manifest['runner_sha256']
    if args.prepare:print('Frozen 36 matched target scores for all three generated violation examples.');return
    assert args.live;g=gateway(manifest['ceiling_usd'])
    cells=list(itertools.product(manifest['examples'],manifest['models'],manifest['targets']))
    cells.sort(key=lambda c:digest(c[0]['example_id']+c[1]+c[2]))
    for i,(example,model,target) in enumerate(cells):
        if i%args.shards!=args.shard:continue
        if STOP.exists():break
        eid='intervention-generated-monitor--'+example['example_id']+'--'+model+'--'+target
        path=BASE/'generated_scores'/(eid+'.json')
        if path.exists():continue
        r={k:v for k,v in example.items() if k!='public_input'};r.update(episode=eid,model=model,target=target,status='started');save(path,r)
        try:r['score']=score(g,model,example['public_input'],BROAD if target=='broad' else SUBSTANTIVE,eid,'pressure_generated_monitor');r['status']='completed'
        except BudgetExceeded:r.update(status='incomplete',error='BudgetExceeded');save(path,r);break
        except Exception as exc:r.update(status='incomplete',error=type(exc).__name__)
        save(path,r);print(eid,r['status'],flush=True)
if __name__=='__main__':main()
