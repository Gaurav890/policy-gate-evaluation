"""New study settings over the existing recorded, budget-controlled transport."""
import urllib.request
from intervention_study.common import BASE, read
from gateway_budget import MODELS, NoRedirect
from gateway_v2 import Gateway
from budget_reconciled import Budget

class StudyOpener:
    def __init__(self):
        self.opener=urllib.request.build_opener(NoRedirect)
    def open(self,request,timeout=None):
        return self.opener.open(request,timeout=180)

def gateway(ceiling):
    cfg=read(BASE/'protocol.json')
    MODELS.update(cfg['models'])
    return Gateway(Budget(ceiling=ceiling),opener=StudyOpener())
