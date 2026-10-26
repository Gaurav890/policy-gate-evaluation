"""Verify distributed files before regenerating derived outputs."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'SHA256SUMS.json').read_text())
for rel,h in manifest.items():
 p=R/rel
 assert p.resolve().is_relative_to(R.resolve()) and p.is_file(),rel
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h,rel
print('Verified',len(manifest),'distributed files.')
