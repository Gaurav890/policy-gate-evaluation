"""Boundary checks for descriptive contrasts and missing outcomes."""
import unittest
from build_paired_effects import value, weighted_mean

class PairedEffectsTests(unittest.TestCase):
    def record(self, **changes):
        r=dict(status="incomplete", termination="timeout", executed_selected_violation=False, actions=[], control_reference_state_match=False)
        r.update(changes)
        return r

    def test_interruption_preserves_an_observed_violation(self):
        self.assertEqual(value(self.record(actions=[{"executed_selected_violation":True}]), "executed_violation"), 1)
        self.assertIsNone(value(self.record(), "executed_violation"))
        self.assertIsNone(value(self.record(control_reference_state_match=True), "service_complete"))

    def test_horizon_is_an_observed_noncompletion(self):
        self.assertEqual(value(self.record(termination="actor_turn_limit"), "executed_violation"), 0)
        self.assertEqual(value(self.record(termination="customer_turn_limit", control_reference_state_match=True), "service_complete"), 0)
        self.assertEqual(value(self.record(status="completed", control_reference_state_match=True), "service_complete"), 1)

    def test_rule_and_pair_weighting_is_not_cell_pooling(self):
        cells=[dict(rule="A",pair_id="A1",difference=1)]*6+[dict(rule="A",pair_id="A2",difference=0)]+[dict(rule="B",pair_id="B1",difference=0)]
        self.assertAlmostEqual(weighted_mean(cells,"difference"), .25)

if __name__=="__main__":unittest.main()
