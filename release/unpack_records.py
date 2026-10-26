"""Verify and unpack the losslessly compressed, anonymized API records."""
import hashlib,json,tarfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
def main():
 manifest=json.loads((R/'release/receipt_manifest.json').read_text())
 count=0
 for name,group in manifest['archives'].items():
  archive=R/name
  assert hashlib.sha256(archive.read_bytes()).hexdigest()==group['sha256'],name
  expected=group['files'];seen=set()
  with tarfile.open(archive,'r:xz') as t:
   for m in t:
    rel=PurePosixPath(m.name)
    assert m.isfile() and not rel.is_absolute() and '..' not in rel.parts and m.name in expected,m.name
    assert m.name not in seen,m.name
    data=t.extractfile(m).read()
    assert hashlib.sha256(data).hexdigest()==expected[m.name],m.name
    dest=R.joinpath(*rel.parts)
    assert dest.resolve().is_relative_to(R.resolve()),m.name
    if dest.exists():assert dest.read_bytes()==data,'Existing record differs: '+m.name
    else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    seen.add(m.name);count+=1
  assert seen==set(expected),name
 print('Verified and unpacked',count,'anonymized API records; no network calls.')
if __name__=='__main__':main()
