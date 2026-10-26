"""Native tests for the version actually used in the online follow-up."""
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from intervention_study.common import BASE,save
from intervention_study.test_intervention import InterventionTests,FakeGateway
from intervention_study.live_gating import runner

class FollowupTests(InterventionTests):
    def run_case(self,case,condition='none',fail=False,limit=6):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name in ['cases.json','native_reference_validation.json']:shutil.copy(BASE/name,root/name)
            save(root/'protocol.json',{})
            cell={k:case[k] for k in ['case_id','pair_id','rule','pressure','domain','split']}
            cell.update(episode='unit',actor='test',condition=condition,repeat=0)
            g=FakeGateway(case,fail)
            with patch.object(runner,'BASE',root),patch.object(runner,'RUNBASE',root):
                rec=runner.run(cell,{'max_actor_turns':32,'max_customer_turns':limit,'gate_model':'gate'},g)
            return rec,g

class MissingOutcomeTests(unittest.TestCase):
    def test_unattempted_cells_are_unresolved(self):
        from intervention_study.live_gating.analyze import summarize
        r=summarize([{'episode':'missing'}],{})
        self.assertEqual(r['violation_rate_bounds'],[0,1])
        self.assertEqual(r['unattempted'],1)
    def test_observed_violation_remains_positive_after_interruption(self):
        from intervention_study.live_gating.analyze import summarize
        record={'episode':'partial','status':'incomplete','executed_selected_violation':True,
            'attempted_selected_violation':True,'actions':[],'gate_failures':0}
        r=summarize([{'episode':'partial'},{'episode':'missing'}],{'partial':record})
        self.assertEqual(r['violation_rate_bounds'],[.5,1])
        self.assertEqual(r['completed'],0)
        self.assertEqual(r['unresolved_violation_outcomes'],1)

if __name__=='__main__':unittest.main()
