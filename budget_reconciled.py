"""Conservative admission using settled response costs and unresolved reservations."""
import fcntl
import hashlib
import json
import math
import os
import uuid
from datetime import datetime,timezone
from pathlib import Path
from gateway_budget import ROOT,BudgetExceeded

class Budget:
    def __init__(self,ceiling=30,ledger=None,records=None,settlements=None):
        authorization=json.loads((ROOT/'groundwork/authorization.json').read_text())
        self.cap=min(float(ceiling),float(authorization['cumulative_usd_cap']))
        self.ledger=Path(ledger or ROOT/'groundwork/spend_ledger.jsonl')
        self.records=Path(records or ROOT/'groundwork/api_records')
        self.settlements=Path(settlements or ROOT/'groundwork/cost_settlements_v003.jsonl')
    def _reconcile(self,entries):
        settled={}
        if self.settlements.exists():
            for line in self.settlements.read_text().splitlines():
                if line:
                    row=json.loads(line)
                    if row['request_id'] in settled:raise ValueError('Duplicate settlement')
                    settled[row['request_id']]=row
        new=[]
        for entry in entries:
            rid=entry['request_id']
            if rid in settled:continue
            path=self.records/(rid+'.json')
            if not path.exists():continue
            raw=path.read_bytes();record=json.loads(raw)
            cost=record.get('response',{}).get('usage',{}).get('cost')
            if record.get('status')!='ok' or cost is None:continue
            if isinstance(cost,bool):raise ValueError('Invalid billed cost')
            cost=float(cost)
            if not math.isfinite(cost) or cost<0:raise ValueError('Invalid billed cost')
            row={'request_id':rid,'response_sha256':hashlib.sha256(raw).hexdigest(),
                 'reported_cost_usd':cost,'held_usd':1.25*cost,
                 'utc':datetime.now(timezone.utc).isoformat(),'method':'reported response cost plus 25 percent margin'}
            settled[rid]=row;new.append(row)
        if new:
            self.settlements.parent.mkdir(parents=True,exist_ok=True)
            with self.settlements.open('a') as f:
                for row in new:f.write(json.dumps(row)+'\n')
                f.flush();os.fsync(f.fileno())
        return sum(settled[e['request_id']]['held_usd'] if e['request_id'] in settled else e['reserved_usd'] for e in entries)
    def reserve(self,payload,rates,metadata):
        bound=len(json.dumps(payload,ensure_ascii=True).encode())+4096
        amount=1.25*(bound*rates['input']+payload['max_tokens']*rates['output'])/1_000_000
        self.ledger.parent.mkdir(parents=True,exist_ok=True)
        with self.ledger.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
            entries=[json.loads(x) for x in f if x.strip()]
            held=self._reconcile(entries)
            if held+amount>self.cap:raise BudgetExceeded(f'Next reservation exceeds ${self.cap:.2f} settled-budget ceiling')
            row={'request_id':uuid.uuid4().hex,'utc':datetime.now(timezone.utc).isoformat(),
                 'reserved_usd':amount,'cumulative_reserved_usd':sum(e['reserved_usd'] for e in entries)+amount,
                 'settled_and_reserved_usd':held+amount,'budget_version':3,
                 'input_token_bound':bound,'max_output_tokens':payload['max_tokens'],'model':payload['model'],**metadata}
            f.write(json.dumps(row)+'\n');f.flush();os.fsync(f.fileno())
        return row
    def total_reserved(self):
        self.ledger.parent.mkdir(parents=True,exist_ok=True)
        with self.ledger.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX);f.seek(0)
            return self._reconcile([json.loads(x) for x in f if x.strip()])
