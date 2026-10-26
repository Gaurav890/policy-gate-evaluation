"""Serialized amended compact collection with independent study and spending locks."""
import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import ROOT, read, save, digest
from intervention_study.live_gating import runner as core
from intervention_study.scaled_design.customer_candidate_v3 import scripted_candidate, model_customer_bounded, VERSION
from intervention_study.scaled_design.shadow import score_record, export_record
from intervention_study.runtime import StudyOpener
from intervention_study.verify_breadth import verify_breadth
from gateway_budget import MODELS
from gateway_v2 import Gateway
from budget_reconciled import Budget

BASE = Path(__file__).resolve().parent


def validate_record(record, base=BASE, cells=None):
    cells = cells or {c['episode']: c for c in read(base/'allocation.json')}
    ep = record['episode']
    if ep not in cells or any(record.get(k) != v for k, v in cells[ep].items()):
        raise ValueError('Unexpected cell metadata')
    imported = read(base/'imports.json')['records'].get(ep)
    if imported:
        if digest(record) != imported['canonical_sha256'] or record['protocol_sha256'] != imported['protocol_sha256']:
            raise ValueError('Imported record changed')
    elif record['protocol_sha256'] != digest(base/'protocol.json'):
        raise ValueError('Unexpected amended protocol')


def retain_stop(value):
    try:
        fd = os.open(BASE/'stop.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, 'w') as stream:
        stream.write(json.dumps(value, indent=2)+'\n'); stream.flush(); os.fsync(stream.fileno())


def verify():
    verify_breadth()
    for name, sha in read(BASE/'freeze.json')['files'].items():
        if digest(ROOT/name) != sha:
            raise ValueError('Frozen source changed: '+name)
    cfg = read(BASE/'protocol.json')
    if digest(BASE/'allocation.json') != cfg['allocation_sha256']:
        raise ValueError('Allocation changed')
    for ep, metadata in read(BASE/'imports.json')['records'].items():
        path = BASE/'episodes'/(ep+'.json')
        if digest(path) != metadata['file_sha256']:
            raise ValueError('Imported episode bytes changed')
    return cfg


def approved_ceiling(base=BASE):
    stage = read(base/'authorization.json')
    if stage.get('approved') is not True or stage.get('scope') != 'compact_live_and_shadow':
        raise PermissionError('Primary collection has not been approved')
    global_approval = read(ROOT/'groundwork/authorization.json')
    if stage.get('protocol_sha256') != digest(base/'protocol.json'):
        raise PermissionError('Approval does not match this protocol')
    ceiling = stage.get('cumulative_ceiling_usd')
    if type(ceiling) not in [int, float] or not 0 < ceiling <= global_approval['cumulative_usd_cap']:
        raise PermissionError('Primary ceiling exceeds recorded project authorization')
    return ceiling


class GuardedGateway(Gateway):
    def complete(self, *args, **kwargs):
        if (BASE/'stop.json').exists():
            raise RuntimeError('Primary collection is stopped')
        try:
            return super().complete(*args, **kwargs)
        except Exception as exc:
            retain_stop( {'error_type': type(exc).__name__, 'episode': kwargs.get('episode'), 'role': kwargs.get('role')})
            raise


def run_cell(cell, cfg, gateway, base=BASE):
    def customer(case, messages, pushbacks):
        if cell['customer'] == 'scripted':
            return {**scripted_candidate(case, messages, pushbacks), 'controller': VERSION+'_scripted'}
        return model_customer_bounded(gateway, case, messages, pushbacks, cell['episode'], cfg['customer_model'])
    with patch.object(core, 'RUNBASE', base), patch.object(core, 'next_turn', customer):
        return core.run({**cell, 'customer_version': VERSION}, cfg, gateway)


def run_shadow(source, case, gateway, cfg, dest):
    rows = export_record(source, case)
    save(dest, {'status': 'prepared', 'rows': rows})
    # Checkpoints own the latest partial rows; exceptions never overwrite them with old rows.
    scored = score_record(source, case, gateway, cfg, checkpoint=lambda items: save(dest, {'status': 'scoring', 'rows': items}))
    complete = all(not d.get('monitor_failure', False) and type(d.get('block')) is bool for row in scored for d in row['decisions'].values())
    save(dest, {'status': 'complete' if complete else 'missing_monitor_output', 'rows': scored})
    return complete


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--check', action='store_true')
    p.add_argument('--live', action='store_true')
    p.add_argument('--phase', choices=['live', 'shadow'], default='live')
    p.add_argument('--limit', type=int)
    args = p.parse_args()
    cfg = verify()
    allocation = read(BASE/'allocation.json')
    if args.check:
        print(json.dumps({'freeze_verified': True, 'assigned': len(allocation), 'authorization': read(BASE/'authorization.json')['approved']})); return
    if not args.live:
        p.error('--check or explicit --live required')
    ceiling = approved_ceiling()
    if args.limit is not None and args.limit <= 0:
        p.error('--limit must be positive')
    if (BASE/'stop.json').exists():
        raise RuntimeError('Inspect and document the retained stop before resumption')
    with (BASE/'.collection.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        unfinished = [p.stem for p in (BASE/'episodes').glob('*.json') if read(p).get('status') == 'started']
        if unfinished:
            retain_stop( {'error_type': 'ProcessInterrupted', 'episodes': unfinished})
            raise RuntimeError('Interrupted attempts retained; document their disposition before resumption')
        # Funding and freeze checks precede loading credentials or making network requests.
        MODELS.update(cfg['models'])
        budget = Budget(ceiling=ceiling)
        gateway = GuardedGateway(budget, opener=StudyOpener())
        cases = {c['case_id']: c for c in read(ROOT/'intervention_study/cases.json')}
        manifest = BASE/'execution.json'
        if not manifest.exists():
            save(manifest, {'held_before_usd': budget.total_reserved(), 'effective_ceiling_usd': budget.cap, 'protocol_sha256': digest(BASE/'protocol.json')})
        done = 0
        for cell in allocation:
            if (BASE/'stop.json').exists() or args.limit is not None and done >= args.limit:
                break
            path = BASE/'episodes'/(cell['episode']+'.json')
            if args.phase == 'live':
                if path.exists():
                    validate_record(read(path)); continue
                try:
                    rec = run_cell(cell, cfg, gateway)
                except Exception as exc:
                    retain_stop( {'episode': cell['episode'], 'error_type': type(exc).__name__}); break
                done += 1
                if rec['gate_failures'] or rec['status'] == 'incomplete' and rec['termination'] not in ['actor_turn_limit', 'customer_turn_limit']:
                    retain_stop( {'episode': cell['episode'], 'error_type': rec['termination'], 'gate_failures': rec['gate_failures']}); break
            elif cell['condition'] == 'none' and path.exists():
                rec = read(path)
                validate_record(rec)
                if rec['status'] == 'started':
                    raise RuntimeError('Source conversation is still started; inspect before shadow scoring')
                dest = BASE/'shadow'/(cell['episode']+'.json')
                if dest.exists():
                    continue
                if not run_shadow(rec, cases[cell['case_id']], gateway, cfg, dest):
                    retain_stop( {'episode': cell['episode'], 'error_type': 'MissingShadowOutput'}); break
                done += 1
        print(json.dumps({'phase': args.phase, 'new_cells': done, 'held_usd': budget.total_reserved(), 'stopped': (BASE/'stop.json').exists()}), flush=True)


if __name__ == '__main__':
    main()
