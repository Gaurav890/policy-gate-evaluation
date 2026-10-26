import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import save
from intervention_study.primary_study import collection_pipeline as p

class PipelineTest(unittest.TestCase):
    def check_case(self,complete,stop):
        calls=[]
        with tempfile.TemporaryDirectory() as td:
            b=Path(td);save(b/'allocation.json',[{'episode':'a'},{'episode':'b'}])
            save(b/'episodes/a.json',{'episode':'a','status':'completed'})
            if complete:save(b/'episodes/b.json',{'episode':'b','status':'completed'})
            if stop:save(b/'stop.json',{'reason':'retained'})
            save(b/'analysis.json',{'recorded':2 if complete else 1})
            with patch.object(p,'BASE',b),patch.object(p,'verify'),patch.object(p,'approved_ceiling'),patch.object(p,'command',side_effect=lambda *a:calls.append(a)):
                p.main()
        return calls
    def test_partial_and_stopped_skip_paid_shadow(self):
        for complete,stop in [(False,False),(True,True)]:
            calls=self.check_case(complete,stop)
            self.assertEqual(len(calls),2)
            self.assertTrue(all('--live' not in c for c in calls))
    def test_finished_live_enters_shadow_then_archives(self):
        calls=self.check_case(True,False)
        self.assertEqual(calls[0],('intervention_study.primary_study.runner','--live','--phase','shadow'))
        self.assertEqual(calls[1],('intervention_study.primary_study.evidence',))
        self.assertEqual(calls[2],('intervention_study.primary_study.analyze','--offline','--native'))

if __name__=='__main__':unittest.main()
