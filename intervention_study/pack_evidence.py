"""Preserve exact new request records separately from the previous paper release."""
import gzip
import hashlib
import json
import re
from intervention_study.common import BASE,ROOT,read,save,digest

def main():
    target=BASE/'evidence';target.mkdir(exist_ok=True)
    lines=[line for line in (ROOT/'groundwork/spend_ledger.jsonl').read_text().splitlines() if json.loads(line).get('role','').startswith('pressure_')]
    rows=[json.loads(line) for line in lines];ids=[r['request_id'] for r in rows];assert len(ids)==len(set(ids))
    keys=[x.split('=',1)[1].strip().strip('"').strip("'") for x in (ROOT/'groundwork/.env').read_text().splitlines() if x.startswith('AI_GATEWAY_API_KEY=')]
    hashes={};archive=target/'api_records.jsonl.gz'
    with archive.open('wb') as stream,gzip.GzipFile(fileobj=stream,mode='wb',filename='',mtime=0) as output:
        for rid in ids:
            assert re.fullmatch('[a-f0-9]{32}',rid)
            path=ROOT/'groundwork/api_records'/(rid+'.json');raw=path.read_bytes();record=json.loads(raw)
            assert record['status']!='reserved','A request is still active'
            assert all(key.encode() not in raw for key in keys if key),'Credential detected'
            hashes[rid]=hashlib.sha256(raw).hexdigest()
            envelope={'request_id':rid,'sha256':hashes[rid],'raw':raw.decode('utf-8')}
            output.write((json.dumps(envelope,ensure_ascii=False,separators=(',',':'))+'\n').encode())
    (target/'new_spend_ledger.jsonl').write_text('\n'.join(lines)+'\n')
    save(target/'baseline_accounting.json',read(BASE/'pilot_summary.json')['spending']['groups']['prior'])
    save(target/'manifest.json',{'record_count':len(ids),'archive_sha256':digest(archive),'ledger_sha256':digest(target/'new_spend_ledger.jsonl'),'baseline_sha256':digest(target/'baseline_accounting.json'),'records':hashes,
         'scope':'Exact local request/response bytes for this development extension, including every failed request. Historical release records remain separate. Provider identifiers and optional reasoning fields are retained locally; this is not an anonymous submission package.'})
    print('Packed',len(ids),'exact records;',archive.stat().st_size,'compressed bytes; credential scan passed.')
if __name__=='__main__':main()
