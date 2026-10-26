"""Synthetic software tests only: no human research judgments are created."""
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
from summarize import load, csv_text, agreement, R
class TestExports(unittest.TestCase):
    def test_round_trip_and_reject_tampering(self):
        rows=[dict(case_id=f'CASE{i:03}',permission='uncertain',block_justification='uncertain',format='uncertain',policy_clause='SOFTWARE TEST',prefix_evidence='SOFTWARE TEST',rationale='=test,"quoted"\nline') for i in range(1,100)]
        raw=csv_text(rows).encode()
        d=dict(packet_sha256=json.loads((R/'review/packet_manifest.json').read_text())['packet_sha256'],reviewer='TEST',experience='SOFTWARE TEST',relationship='external',independent=True,attest=True,rows=rows,case_count=99,csv_sha256=hashlib.sha256(raw).hexdigest())
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'review-TEST-submission.json';c=p.with_name('review-TEST.csv');c.write_bytes(raw);p.write_text(json.dumps(d));self.assertEqual(len(load(p)[1]),99)
            for mutate in [lambda x:x.update(packet_sha256='bad'),lambda x:x['rows'].pop(),lambda x:x['rows'][0].update(permission='bad'),lambda x:x['rows'][0].update(rationale='changed')]:
                wrong=copy.deepcopy(d);mutate(wrong);p.write_text(json.dumps(wrong))
                with self.assertRaises(AssertionError):load(p)
    def test_agreement(self):
        self.assertEqual(agreement(['a','b'],['a','b'])['cohen_kappa'],1)
        self.assertEqual(agreement(['a','b'],['b','a'])['cohen_kappa'],-1)
        self.assertIsNone(agreement(['uncertain'],['uncertain'])['cohen_kappa'])
if __name__=='__main__':unittest.main()
