"""Check that monitor views are causal and exclude private task metadata."""

import copy
import unittest

from run_monitors import prefix_views


class PrefixTests(unittest.TestCase):
    def example(self):
        return {"policy": "current policy", "tools": [], "grading": {"reward": "SECRET"},
                "name_map": {"private": "SECRET"}, "canonical_messages": ["SECRET"],
                "simulation": {"messages": [
                    {"role": "user", "content": "Help me"},
                    {"role": "assistant", "content": None, "raw_data": {"request_record": "r"},
                     "tool_calls": [{"name": "lookup", "arguments": {"x": 1}}]},
                    {"role": "tool", "content": "FUTURE", "error": True},
                    {"role": "assistant", "content": "Recovered", "raw_data": {"request_record": "s"}},
                ]}}

    def test_future_and_hidden_data_do_not_change_first_view(self):
        one = self.example()
        two = copy.deepcopy(one)
        two["grading"] = {"different": "label"}
        two["simulation"]["messages"][2]["content"] = "changed future"
        self.assertEqual(next(prefix_views(one)), next(prefix_views(two)))
        text = str(next(prefix_views(one))["input"])
        self.assertNotIn("SECRET", text)
        self.assertNotIn("FUTURE", text)

    def test_error_is_visible_only_after_observation(self):
        views = list(prefix_views(self.example()))
        self.assertEqual(views[0]["rules"]["any_observed_tool_error"], 0)
        self.assertEqual(views[1]["rules"]["any_observed_tool_error"], 1)


if __name__ == "__main__":
    unittest.main()
