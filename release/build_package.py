"""Build the anonymous supplement from an explicit source-file allowlist.

Run in the research workspace, which holds the original API records. Reviewers
should use reproduce.sh; rebuilding this distributor archive is not required.
"""
import gzip,hashlib,io,json,lzma,re,shutil,tarfile,tempfile,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
DROP={'generationId','providerResponseId','clientSessionId','clientSessionIdSource','system_fingerprint','reasoning','reasoning_details','provider_metadata','providerMetadata','response_headers','logical_request_id'}
def sanitize(value,response=False):
 if isinstance(value,list):return [sanitize(x) for x in value]
 if isinstance(value,dict):return {k:sanitize(v,k=='response') for k,v in value.items() if k not in DROP and not(response and k=='id')}
 return value
def dump(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 cfg=json.loads((R/'release/source_files.json').read_text());groups=json.loads((R/'release/receipt_groups.json').read_text())
 out=Path(tempfile.mkdtemp(prefix='monitor-audit-release-'))
 for target,source in cfg.items():
  dest=out/target;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/source,dest)
 transformations=[];manifest={'format':'Lossless xz-compressed tar archives of anonymized JSON records','archives':{}}
 for group,ids in groups.items():
  name=f'release/api_records_{group}.tar.xz';archive=out/name;archive.parent.mkdir(exist_ok=True)
  prefix=({'original':'groundwork/api_records','additional':'substantive_evaluation/api_records'}.get(group) or f'intervention_study/released_api_records/{group}')
  files={}
  # Neighboring record IDs are not chronological. Sort by episode and role to
  # compress repeated conversations together without changing any JSON content.
  rows=[]
  for rid in ids:
   source=R/'groundwork/api_records'/f'{rid}.json';raw=source.read_bytes();q=json.loads(raw)
   rows.append((str(q.get('episode','')),str(q.get('role','')),rid,raw,q))
  with lzma.open(archive,'wb',preset=3) as xz:
   with tarfile.open(fileobj=xz,mode='w|') as tar:
    for _,__,rid,raw,q in sorted(rows):
     data=(json.dumps(sanitize(q),indent=2,ensure_ascii=False)+'\n').encode();rel=f'{prefix}/{rid}.json'
     entry=tarfile.TarInfo(rel);entry.size=len(data);entry.mode=0o644;entry.mtime=0
     tar.addfile(entry,io.BytesIO(data));files[rel]=sha(data)
     transformations.append({'file':rel,'original_sha256':sha(raw),'released_sha256':sha(data)})
  manifest['archives'][name]={'sha256':sha(archive.read_bytes()),'files':files}
  print(group,len(ids),'records;',archive.stat().st_size,'bytes',flush=True)
 dump(out/'release/receipt_manifest.json',manifest)
 dump(out/'release_transformations.json',{'scope':'API-response transport metadata and optional reasoning fields omitted. Scientific prompts, visible completions, tools, usage, local record IDs and risk scores retained. The resulting JSON bytes are compressed losslessly in separate cohort archives. The original partition preserves the earlier cumulative-cost verifier.','omitted_fields':sorted(DROP|{'response.id'}),'files':transformations})
 # Scan uncompressed evidence and source files, including the receipt contents.
 tokens=[x.encode() for x in json.loads((R/'submission/anonymity_tokens.json').read_text())]
 keyfile=R/'groundwork/.env'
 if keyfile.exists():
  for line in keyfile.read_text().splitlines():
   if line.strip().startswith('AI_GATEWAY_API_KEY='):
    key=line.split('=',1)[1].strip().strip('\"').strip("'")
    if len(key)>15:tokens.append(key.encode())
 def check(data,name):
  assert not any(t.lower() in data.lower() for t in tokens),'Identity/credential scan failed: '+name
 for p in out.rglob('*'):
  if p.is_file() and p.suffix!='.xz':check(p.read_bytes(),str(p.relative_to(out)))
 for name in manifest['archives']:
  with tarfile.open(out/name,'r:xz') as t:
   for m in t:check(t.extractfile(m).read(),m.name)
 inventory={str(p.relative_to(out)):sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}
 dump(out/'SHA256SUMS.json',inventory)
 target=R/'submission/supplement.next.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(out.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(out))
 assert target.stat().st_size<100_000_000, target.stat().st_size
 dump(R/'submission/package_build.json',{'candidate':'submission/supplement.next.zip','bytes':target.stat().st_size,'sha256':sha(target.read_bytes()),'distributed_files':len(inventory)+1,'api_records':sum(map(len,groups.values())),'identity_and_credential_scan':'passed','paid_calls':0})
 print('Candidate package:',target.stat().st_size,'bytes; anonymity scan passed.',flush=True)
 shutil.rmtree(out)
if __name__=='__main__':main()
