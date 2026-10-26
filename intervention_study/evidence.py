"""Read exact recorded response bytes from local files or a verified offline archive."""
import functools
import gzip
import hashlib
import json
from intervention_study.common import BASE,ROOT,read,digest

@functools.lru_cache(maxsize=1)
def archive():
    meta=read(BASE/'evidence/manifest.json');path=BASE/'evidence/api_records.jsonl.gz'
    assert digest(path)==meta['archive_sha256']
    assert digest(BASE/'evidence/new_spend_ledger.jsonl')==meta['ledger_sha256']
    assert digest(BASE/'evidence/baseline_accounting.json')==meta['baseline_sha256']
    records={}
    with gzip.open(path,'rt',encoding='utf-8') as f:
        for line in f:
            row=json.loads(line);raw=row['raw'].encode();rid=row['request_id']
            assert hashlib.sha256(raw).hexdigest()==row['sha256']==meta['records'][rid]
            rec=json.loads(raw);assert rec['request_id']==rid and rid not in records
            records[rid]=rec
    assert len(records)==meta['record_count']
    return records

def receipt(rid):
    local=ROOT/'groundwork/api_records'/(rid+'.json')
    if local.exists():return read(local)
    return archive()[rid]
