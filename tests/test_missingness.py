import unittest
from study.analyze_confirmatory import alert_summary_identified
class MissingnessTests(unittest.TestCase):
    def test_unknown_later_score_does_not_change_first_or_any_alert(self):
        self.assertTrue(alert_summary_identified(3,2,[9],[4]))
    def test_unknown_earlier_score_leaves_first_alert_undefined(self):
        self.assertFalse(alert_summary_identified(3,2,[3],[4]))
    def test_no_observed_alert_cannot_be_treated_as_negative_with_missing_score(self):
        self.assertFalse(alert_summary_identified(3,2,[9],[]))
    def test_unaccounted_prefix_is_incomplete(self):
        self.assertFalse(alert_summary_identified(4,2,[9],[4]))
    def test_full_coverage_identifies_no_alert(self):
        self.assertTrue(alert_summary_identified(3,3,[],[]))
