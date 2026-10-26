import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import save,read,digest
from intervention_study.primary_study import monitor_progress as m

class ProgressTests(unittest.TestCase):
    def test_started_is_pending_and_customer_flags_do_not_stop(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'protocol.json',{});sha=digest(b/'protocol.json')
            for ep,status in [('a','completed'),('b','started')]:
                save(b/('episodes/'+ep+'.json'),{'episode':ep,'case_id':'case','protocol_sha256':sha,'status':status,'actions':[]})
            checked={}
            with patch.object(m,'BASE',b),patch.object(m,'verify'),patch.object(m,'replay',return_value={'ok':True}) as replay,patch.object(m,'audit',return_value={'flagged':True}):
                m.inspect(checked,{'case':{}},{e:{'episode':e} for e in ['a','b']},{})
                self.assertEqual(replay.call_count,1);self.assertEqual(set(checked),{'a'})
                self.assertFalse((b/'stop.json').exists())
                rec=read(b/'episodes/a.json');rec['actions']=[{'changed':True}];save(b/'episodes/a.json',rec)
                with self.assertRaises(ValueError):m.inspect(checked,{'case':{}},{e:{'episode':e} for e in ['a','b']},{})
    def test_integrity_failure_preserves_existing_stop(self):
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'stop.json',{'error_type':'EarlierError'})
            with patch.object(m,'BASE',b):m.stop_for_integrity('Mismatch')
            self.assertEqual(read(b/'stop.json')['error_type'],'EarlierError')
            self.assertEqual(read(b/'integrity_failure.json')['error_type'],'Mismatch')

if __name__=='__main__':unittest.main()
