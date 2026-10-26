import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gateway_budget import ROOT,MODELS,write_json
from budget_reconciled import Budget
from gateway_v2 import Gateway
BASE=ROOT/'replication'
def plan():return json.loads((BASE/'plan.json').read_text())
def gateway():
 MODELS.update(plan()['models'])
 cap=json.loads((ROOT/'groundwork/authorization.json').read_text())['cumulative_usd_cap']
 return Gateway(Budget(ceiling=cap))
def freeze(label,sources,create=False):
 value={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}
 p=BASE/(label+'_freeze.json')
 if create and not p.exists():write_json(p,value)
 assert json.loads(p.read_text())==value,'Frozen source changed: '+label
 return value
SOURCES=['replication/plan.json','replication/common.py','gateway_v2.py','gateway_budget.py','budget_reconciled.py','benchmark_adapter.py','run_monitors.py']
