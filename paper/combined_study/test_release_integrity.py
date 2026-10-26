import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import release_integrity as ri
class ReleasedBytes(unittest.TestCase):
 def test_public_administrative_redaction(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'release').mkdir();p=root/'authorization.json'
   p.write_bytes(b'{"authorization":"[redacted]"}')
   original=ri.digest(b'private original');released=ri.digest(p.read_bytes())
   (root/'release/public_file_transformations.json').write_text(json.dumps({'records':{'authorization.json':{'original_sha256':original,'released_sha256':released}}}))
   with patch.object(ri,'ROOT',root),patch.object(ri,'MAP',root/'missing.json'):
    ri.mapping.cache_clear();ri.verify_file(p,original)
    with self.assertRaises(AssertionError):ri.verify_file(p,released)
    p.write_bytes(b'changed')
    with self.assertRaises(AssertionError):ri.verify_file(p,original)
   ri.mapping.cache_clear()
 def test_original_and_transformed(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);p=root/'receipt.zip';p.write_bytes(b'released');m=root/'mapping.json';original=hashlib.sha256(b'original').hexdigest();released=ri.digest(b'released')
   with patch.object(ri,'ROOT',root),patch.object(ri,'MAP',m):
    ri.mapping.cache_clear();ri.verify_file(p,released)
    m.write_text(json.dumps({'archive':'receipt.zip','original_archive_sha256':original,'released_archive_sha256':released,'records':{'r':{'original_sha256':original,'released_sha256':released}}}));ri.mapping.cache_clear()
    ri.verify_file(p,original);ri.verify_receipt('r',b'released',original)
    with self.assertRaises(AssertionError):ri.verify_receipt('r',b'changed',original)
    with self.assertRaises(AssertionError):ri.verify_receipt('r',b'released',released)
    p.write_bytes(b'changed')
    with self.assertRaises(AssertionError):ri.verify_file(p,original)
   ri.mapping.cache_clear()
if __name__=='__main__':unittest.main()
