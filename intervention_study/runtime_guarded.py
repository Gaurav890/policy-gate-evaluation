"""Development recovery transport: connection preflight and shared failure stop."""
import hashlib
import json
import socket
import urllib.error
import urllib.request
from datetime import datetime, timezone
from intervention_study.common import BASE, read, save
from intervention_study.runtime import StudyOpener
from gateway_budget import MODELS
from gateway_v2 import Gateway
from budget_reconciled import Budget
STOP=BASE/'recovery_stop.json'
class GuardStopped(RuntimeError):pass

def stop(reason):
    try:
        with STOP.open('x') as f:json.dump({'utc':datetime.now(timezone.utc).isoformat(),'reason':reason},f)
    except FileExistsError:pass

class DiagnosticOpener(StudyOpener):
    def open(self,request,timeout=None):
        try:return super().open(request,timeout)
        except Exception as exc:
            detail={'utc':datetime.now(timezone.utc).isoformat(),'payload_sha256':hashlib.sha256(request.data or b'').hexdigest(),'exception':type(exc).__name__,'reason':str(getattr(exc,'reason',exc))[:1000]}
            with (BASE/'transport_diagnostics.jsonl').open('a') as f:f.write(json.dumps(detail)+'\n')
            stop('Inference transport failure: '+type(exc).__name__)
            raise

class GuardedGateway(Gateway):
    def complete(self,*args,**kwargs):
        if STOP.exists():raise GuardStopped('Shared pilot stop: inspect recovery_stop.json')
        try:
            socket.getaddrinfo('ai-gateway.vercel.sh',443)
            with urllib.request.urlopen('https://ai-gateway.vercel.sh/v1/models',timeout=15) as response:assert response.status==200
        except Exception as exc:
            stop('Free preflight failed: '+type(exc).__name__+': '+str(exc)[:500]);raise GuardStopped('Connection preflight failed; no inference reservation made') from None
        try:return super().complete(*args,**kwargs)
        except Exception:
            stop('Inference request did not return a usable output; inspect the retained record.')
            raise

def gateway(ceiling):
    cfg=read(BASE/'protocol_v2.json');MODELS.update(cfg['models'])
    return GuardedGateway(Budget(ceiling=ceiling),opener=DiagnosticOpener())
