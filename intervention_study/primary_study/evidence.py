"""Bounded-memory receipts, exact archives and inclusive cost accounting."""
import argparse
import fcntl
import hashlib
import json
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
import zipfile
from intervention_study.common import ROOT, read, save, digest

BASE = Path(__file__).resolve().parent


def stage_ledger(base=BASE, offline=False):
    path = base/'evidence'/read(base/'evidence/manifest.json')['ledger'] if offline else ROOT/'groundwork/spend_ledger.jsonl'
    ids = {c['episode'] for c in read(base/'allocation.json')}
    return [e for e in (json.loads(s) for s in path.read_text().splitlines()) if e.get('episode', '').removesuffix('--shadow') in ids] if path.exists() else []


class Receipts:
    def __init__(self, base=BASE, offline=False):
        self.base, self.offline = base, offline
        self.meta = read(base/'evidence/manifest.json') if offline else None
        self.archive = None
        if offline:
            path = base/'evidence'/self.meta['archive']
            if digest(path) != self.meta['archive_sha256'] or digest(base/'evidence'/self.meta['ledger']) != self.meta['ledger_sha256']:
                raise ValueError('Evidence archive changed')
            self.archive = zipfile.ZipFile(path)

    @lru_cache(maxsize=64)
    def __getitem__(self, rid):
        raw = self.archive.read(rid+'.json') if self.offline else (ROOT/'groundwork/api_records'/(rid+'.json')).read_bytes()
        if self.offline and hashlib.sha256(raw).hexdigest() != self.meta['records'][rid]:
            raise ValueError('Receipt hash mismatch')
        row = json.loads(raw)
        if row['request_id'] != rid:
            raise ValueError('Receipt identity mismatch')
        return row

    def __contains__(self, rid):
        return rid in self.meta['records'] if self.offline else (ROOT/'groundwork/api_records'/(rid+'.json')).exists()


def costs(entries, receipts):
    grouped = {}
    for e in entries:
        rec = receipts[e['request_id']]; u = rec.get('response', {}).get('usage', {})
        value = u.get('cost'); known = rec.get('status') == 'ok' and value is not None
        role = 'shadow' if e['episode'].endswith('--shadow') else 'actor' if e['role'] == 'live_gating_actor' else 'customer' if e['role'] == 'scaled_customer' else 'live_gate'
        episode = e['episode'].removesuffix('--shadow')
        row = grouped.setdefault(episode, {k: {'requests': 0, 'reported_usd': Decimal(0), 'unresolved_reservation_usd': Decimal(0), 'unknown_cost_requests': 0} for k in ['actor', 'customer', 'live_gate', 'shadow']})[role]
        row['requests'] += 1
        if value is not None:
            row['reported_usd'] += Decimal(str(value))
        if not known:
            row['unknown_cost_requests'] += 1; row['unresolved_reservation_usd'] += Decimal(str(e['reserved_usd']))
    return {ep: {role: {k: float(v) if isinstance(v, Decimal) else v for k, v in r.items()} for role, r in roles.items()} for ep, roles in grouped.items()}


def pack(base=BASE):
    with (base/'.collection.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        rows = stage_ledger(base); seen = set(); hashes = {}
        for row in rows:
            rid = row['request_id']
            if rid in seen: raise ValueError('Duplicate ledger request')
            seen.add(rid); hashes[rid] = digest(ROOT/'groundwork/api_records'/(rid+'.json'))
        dest = base/'evidence'; dest.mkdir(exist_ok=True)
        ledger = '\n'.join(json.dumps(r) for r in rows)+ ('\n' if rows else '')
        version = digest({'receipts': hashes, 'ledger': ledger})[:16]
        name = 'api_records-'+version+'.zip'
        if not (dest/name).exists():
            with zipfile.ZipFile(dest/name, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for rid in hashes:
                    raw = (ROOT/'groundwork/api_records'/(rid+'.json')).read_bytes()
                    assert hashlib.sha256(raw).hexdigest() == hashes[rid]
                    info = zipfile.ZipInfo(rid+'.json', date_time=(1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, raw)
        ledger_name = 'ledger-'+version+'.jsonl'
        (dest/ledger_name).write_text(ledger)
        meta = {'archive': name, 'archive_sha256': digest(dest/name), 'ledger': ledger_name, 'ledger_sha256': digest(dest/ledger_name), 'records': hashes,
                'scope': 'Exact private receipts, including failed or abandoned reservations. Not an anonymous release.'}
        save(dest/('manifest-'+version+'.json'), meta); save(dest/'manifest.json', meta)
        print('Archived', len(rows), 'primary receipts without model requests.')


if __name__ == '__main__':
    pack()
