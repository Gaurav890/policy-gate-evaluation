"""Cost-pilot adapter over preserved live execution; full evaluation remains locked."""
import argparse,json,hashlib,socket,urllib.request
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import ROOT,read,save,digest
from intervention_study.live_gating import runner as core
from intervention_study.runtime import StudyOpener
from gateway_budget import MODELS
from gateway_v2 import Gateway
from budget_reconciled import Budget
from intervention_study.scaled_design.customer import scripted,model_customer
from intervention_study.scaled_design.shadow import export_record,score_record
BASE=Path(__file__).resolve().parent
STOP=BASE/'pilot_stop.json'

def verify():
 frozen=read(BASE/'pilot_freeze.json')
 for rel,h in frozen['files'].items():assert digest(ROOT/rel)==h,rel
 from intervention_study.verify_breadth import verify_breadth
 verify_breadth()
 return read(BASE/'protocol.json')

class GuardedGateway(Gateway):
 def complete(self,*args,**kwargs):
  if STOP.exists():raise RuntimeError('Inspect pilot_stop.json before resuming')
  try:return super().complete(*args,**kwargs)
  except Exception as exc:
   save(STOP,{'status':'stop','error_type':type(exc).__name__,'episode':kwargs.get('episode'),'role':kwargs.get('role')});raise

def run_cell(cell,cfg,g):
 # Serial-only adapter: frozen core source is unchanged and its hash is recorded.
 # The customer receives neither environment state nor reference success labels.
 def customer(case,messages,pushbacks):
  return scripted(case,messages,pushbacks) if cell['customer']=='scripted' else model_customer(g,case,messages,pushbacks,cell['episode'],cfg['customer_model'])
 with patch.object(core,'RUNBASE',BASE),patch.object(core,'next_turn',customer):
  return core.run(cell,cfg,g)

def main():
 p=argparse.ArgumentParser();p.add_argument('--live',action='store_true');p.add_argument('--pilot',action='store_true');p.add_argument('--ceiling-usd',type=float,default=100);p.add_argument('--limit',type=int);args=p.parse_args()
 if not (args.live and args.pilot):p.error('Only --live --pilot is implemented; evaluation remains locked')
 if not 0<args.ceiling_usd<=125:p.error('This pilot has a maximum proposed ceiling of $125; actual authorization is independently enforced')
 cfg=verify()
 if STOP.exists():raise RuntimeError('Resolve the recorded pilot stop before any resumption')
 # Free connectivity/catalog preflight occurs before loading the project key.
 socket.getaddrinfo('ai-gateway.vercel.sh',443)
 with urllib.request.urlopen('https://ai-gateway.vercel.sh/v1/models',timeout=20) as r:available={m['id'] for m in json.load(r)['data']}
 assert all(m['id'] in available for m in cfg['models'].values())
 MODELS.update(cfg['models']);budget=Budget(ceiling=args.ceiling_usd);g=GuardedGateway(budget,opener=StudyOpener())
 save(BASE/'pilot_execution.json',{'effective_cumulative_ceiling_usd':budget.cap,'held_before_usd':budget.total_reserved(),'protocol_sha256':digest(BASE/'protocol.json'),'full_evaluation_locked':True})
 cases={c['case_id']:c for c in read(ROOT/'intervention_study/cases.json')};count=0
 for cell in read(BASE/'pilot_allocation.json'):
  if STOP.exists():break
  if args.limit is not None and count>=args.limit:break
  path=BASE/'episodes'/(cell['episode']+'.json')
  rec=read(path) if path.exists() else run_cell(cell,cfg,g)
  count+=1
  if rec['status']=='incomplete' and rec['termination'] not in ['actor_turn_limit','customer_turn_limit']:
   save(STOP,{'status':'stop','episode':cell['episode'],'error_type':rec['termination']});break
  if cell['condition']=='none':
   dest=BASE/'shadow'/(cell['episode']+'.json')
   if dest.exists():continue
   # Retain matched proposals before scoring; a scored failure is never retried silently.
   rows=export_record(rec,cases[cell['case_id']]);save(dest,{'status':'started','rows':rows})
   try:
    scored=score_record(rec,cases[cell['case_id']],g,cfg,checkpoint=lambda items:save(dest,{'status':'scoring','rows':items}))
    save(dest,{'status':'complete' if all(not d.get('monitor_failure') for row in scored for d in row['decisions'].values()) else 'missing_monitor_output','rows':scored})
   except Exception as exc:
    save(dest,{'status':'interrupted','error_type':type(exc).__name__,'rows':rows});raise
 print('Cost-pilot checkpoint saved. Full evaluation remains locked.')
if __name__=='__main__':main()
