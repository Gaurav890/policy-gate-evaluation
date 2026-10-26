import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from budget_reconciled import Budget,BudgetExceeded

class SettlementTests(unittest.TestCase):
    def test_reservation_only_released_with_recorded_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);records=root/'records';records.mkdir()
            b=Budget(.1,root/'ledger',records,root/'settlements')
            payload={'model':'test','max_tokens':100};rates={'input':2,'output':10}
            one=b.reserve(payload,rates,{})
            self.assertEqual(b.total_reserved(),one['reserved_usd'])
            (records/(one['request_id']+'.json')).write_text(json.dumps({'status':'request_failed'}))
            self.assertEqual(b.total_reserved(),one['reserved_usd'])
            (records/(one['request_id']+'.json')).write_text(json.dumps({'status':'ok','response':{'usage':{'cost':.002}}}))
            self.assertEqual(b.total_reserved(),.0025)
            self.assertEqual(Budget(.1,root/'ledger',records,root/'settlements').total_reserved(),.0025)
            self.assertEqual(len((root/'settlements').read_text().splitlines()),1)
    def test_cap_cannot_be_raised_and_unsettled_requests_still_block(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "groundwork").mkdir()
            authorization = root / "groundwork" / "authorization.json"
            authorization.write_text(json.dumps({"cumulative_usd_cap": 30}))
            with patch("budget_reconciled.ROOT", root):
                self.assertEqual(Budget(ceiling=100).cap, 30)
                self.assertEqual(Budget(ceiling=5).cap, 5)
                authorization.write_text(json.dumps({"cumulative_usd_cap": 100}))
                self.assertEqual(Budget(ceiling=200).cap, 100)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);b=Budget(.012,root/'ledger',root/'records',root/'settlements')
            b.reserve({'model':'test','max_tokens':100},{'input':2,'output':10},{})
            with self.assertRaises(BudgetExceeded):b.reserve({'model':'test','max_tokens':100},{'input':2,'output':10},{})

if __name__=='__main__':unittest.main()
