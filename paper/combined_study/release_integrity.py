"""Verify released bytes separately from original receipt commitments."""
import hashlib,json
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
MAP=ROOT/'release/compact_receipt_transformations.json'

def digest(raw):return hashlib.sha256(raw).hexdigest()
@lru_cache(maxsize=1)
def mapping():return json.loads(MAP.read_text()) if MAP.exists() else None

def original_commitment(path):
    raw=path.read_bytes();m=mapping();name=str(path.relative_to(ROOT))
    public_map=ROOT/'release/public_file_transformations.json'
    if public_map.exists():
        records=json.loads(public_map.read_text())['records']
        if name in records:
            record=records[name]
            assert digest(raw)==record['released_sha256'],'Released administrative bytes changed'
            return record['original_sha256']
    if m and name==m['archive']:
        assert digest(raw)==m['released_archive_sha256'],'Released archive bytes changed'
        return m['original_archive_sha256']
    return digest(raw)

def verify_file(path,expected):
    assert original_commitment(path)==expected,str(path.relative_to(ROOT))

def verify_receipt(rid,raw,expected):
    m=mapping()
    if m:
        record=m['records'][rid]
        assert record['original_sha256']==expected,'Original receipt commitment differs'
        assert digest(raw)==record['released_sha256'],'Released receipt bytes changed'
    else:assert digest(raw)==expected,'Original receipt bytes changed'
