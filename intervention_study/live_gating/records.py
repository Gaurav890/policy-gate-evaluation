"""Exact offline evidence for this follow-up, separate from earlier releases."""
import gzip
import hashlib
import json
from functools import lru_cache
from intervention_study.common import BASE,ROOT,read,save,digest
RUNBASE=BASE/'live_gating'

@lru_cache(maxsize=1)
def archive():
    meta=read(RUNBASE/'evidence/manifest.json');path=RUNBASE/'evidence/api_records.jsonl.gz'
    assert digest(path)==meta['archive_sha256']
    assert digest(RUNBASE/'evidence/ledger.jsonl')==meta['ledger_sha256']
    records={}
    with gzip.open(path,'rt') as f:
        for line in f:
            entry=json.loads(line);rid=entry['request_id'];raw=entry['raw'].encode()
            assert hashlib.sha256(raw).hexdigest()==entry['sha256']==meta['records'][rid]
            assert rid not in records;records[rid]=json.loads(raw)
    assert len(records)==meta['record_count']
    return records

def receipt(rid):
    path=ROOT/'groundwork/api_records'/(rid+'.json')
    return read(path) if path.exists() else archive()[rid]

def pack():
    dest=RUNBASE/'evidence';dest.mkdir(exist_ok=True)
    lines=[s for s in (ROOT/'groundwork/spend_ledger.jsonl').read_text().splitlines() if json.loads(s).get('episode','').startswith('live-gating-20261011--')]
    hashes={};path=dest/'api_records.jsonl.gz'
    with path.open('wb') as f,gzip.GzipFile(fileobj=f,filename='',mtime=0,mode='wb') as out:
        for line in lines:
            rid=json.loads(line)['request_id'];raw=(ROOT/'groundwork/api_records'/(rid+'.json')).read_bytes()
            assert json.loads(raw)['status']!='reserved','A request is active'
            assert rid not in hashes;hashes[rid]=hashlib.sha256(raw).hexdigest()
            out.write((json.dumps({'request_id':rid,'sha256':hashes[rid],'raw':raw.decode()},ensure_ascii=False)+'\n').encode())
    (dest/'ledger.jsonl').write_text('\n'.join(lines)+'\n')
    save(dest/'manifest.json',{'archive_sha256':digest(path),'ledger_sha256':digest(dest/'ledger.jsonl'),'record_count':len(hashes),'records':hashes,'scope':'Private exact records, including provider metadata; not an anonymous submission supplement.'})
    print('Archived',len(hashes),'follow-up API records.')

if __name__=='__main__':pack()
