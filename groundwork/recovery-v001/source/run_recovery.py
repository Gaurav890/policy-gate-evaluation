"""One explicitly recorded new attempt for the v001 infrastructure interruption."""
import hashlib
from gateway_budget import ROOT, Budget, write_json
from gateway_v2 import Gateway
from run_development import run_episode

class RecoveryGateway(Gateway):
    def complete(self,*args,**kwargs):
        kwargs['episode']='recovery-v001:'+kwargs.get('episode','')
        return super().complete(*args,**kwargs)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--live',action='store_true');args=parser.parse_args()
    if not args.live:raise SystemExit('Explicit --live required')
    out=ROOT/'groundwork/recovery-v001';out.mkdir(exist_ok=True)
    write_json(out/'provenance.json',{'reason':'HTTP 429 in original attempt',
        'original':'development-v001/airline-33-deepseek-rename.json','new_attempt':True,
        'settings':'Original v001 prompts, tools, models, and parallel-call behavior; bounded transport retries added',
        'source_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('gateway_v2.py','gateway_budget.py','benchmark_adapter.py','run_development.py','run_recovery.py')}})
    run_episode(RecoveryGateway(Budget(ceiling=22)), 'airline','33','deepseek',True,out)
