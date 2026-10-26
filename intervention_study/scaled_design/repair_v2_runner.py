"""Six prospective engineering checks under the approved pilot ceiling."""
import argparse
from unittest.mock import patch
from intervention_study.common import read, save, digest, ROOT
from intervention_study.scaled_design.runner import verify, BASE as PARENT
from intervention_study.scaled_design.customer_candidate_v3 import scripted_candidate, model_customer_bounded as model_customer_candidate, VERSION
from intervention_study.live_gating import runner as core
from intervention_study.runtime import StudyOpener
from gateway_budget import MODELS
from gateway_v2 import Gateway
from budget_reconciled import Budget

BASE = PARENT / 'repair_validation_v2'
STOP = BASE / 'stop.json'


class RepairGateway(Gateway):
    def complete(self, *args, **kwargs):
        if STOP.exists():
            raise RuntimeError('Inspect the retained repair-validation failure before resuming')
        try:
            return super().complete(*args, **kwargs)
        except Exception as exc:
            save(STOP, {'error_type': type(exc).__name__, 'episode': kwargs.get('episode'), 'role': kwargs.get('role')})
            raise


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--live', action='store_true')
    args = p.parse_args()
    if not args.live:
        p.error('Explicit --live is required')
    verify()
    for rel, sha in read(BASE / 'freeze.json')['files'].items():
        assert digest(ROOT / rel) == sha, rel
    assert not STOP.exists()
    cfg = read(BASE / 'protocol.json')
    allocation = read(BASE / 'pilot_allocation.json')
    assert len(allocation) == 6
    MODELS.update(cfg['models'])
    budget = Budget(ceiling=125)
    g = RepairGateway(budget, opener=StudyOpener())
    save(BASE / 'execution.json', {'effective_cumulative_ceiling_usd': budget.cap, 'held_before_usd': budget.total_reserved(),
                                 'scope': 'Targeted pilot engineering repairs; original 20-cell allocation preserved; no primary collection.'})
    for cell in allocation:
        if STOP.exists():
            break
        path = BASE / 'episodes' / (cell['episode'] + '.json')
        if path.exists():
            continue
        def customer(case, messages, pushbacks):
            if cell['customer'] == 'scripted':
                return {**scripted_candidate(case, messages, pushbacks), 'controller': VERSION + '_scripted'}
            return model_customer_candidate(g, case, messages, pushbacks, cell['episode'], cfg['customer_model'])
        with patch.object(core, 'RUNBASE', BASE), patch.object(core, 'next_turn', customer):
            rec = core.run({**cell, 'customer_version': VERSION}, cfg, g)
        if rec['status'] == 'incomplete' and rec['termination'] not in ['actor_turn_limit', 'customer_turn_limit']:
            save(STOP, {'episode': cell['episode'], 'error_type': rec['termination']})
            break
    print('Engineering checkpoint saved. Full evaluation remains locked.', flush=True)


if __name__ == '__main__':
    main()
