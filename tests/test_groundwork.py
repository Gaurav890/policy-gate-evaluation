"""Offline tests of semantic preservation, leakage prevention, and cost caps."""

import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from gateway_budget import Budget, BudgetExceeded
from benchmark_adapter import (ROOT, ToolCall, AssistantMessage, load_task,
                               make_environment, grade_deterministic)


class GroundworkTests(unittest.TestCase):
    def test_budget_is_persistent_and_never_refunds(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "ledger.jsonl"
            first = Budget(path, ceiling=0.1)
            payload = {"model": "test", "max_tokens": 100}
            rates = {"input": 2.0, "output": 10.0}
            first.reserve(payload, rates, {})
            self.assertGreater(Budget(path, 0.1).total_reserved(), 0)
            with self.assertRaises(BudgetExceeded):
                Budget(path, 0.001).reserve(payload, rates, {})

    def test_authorization_cannot_be_raised_by_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "groundwork").mkdir()
            authorization = root / "groundwork" / "authorization.json"
            authorization.write_text(json.dumps({"cumulative_usd_cap": 30}))
            with patch("gateway_budget.ROOT", root):
                self.assertEqual(Budget(ceiling=100).cap, 30)
                self.assertEqual(Budget(ceiling=5).cap, 5)
                authorization.write_text(json.dumps({"cumulative_usd_cap": 100}))
                self.assertEqual(Budget(ceiling=200).cap, 100)

    def test_rejects_reserved_task(self):
        manifest = json.loads((ROOT / "pilot_manifest.json").read_text())
        task_id = manifest["domains"]["airline"]["reserved_upstream_test_ids"][0]
        with self.assertRaises(ValueError):
            load_task("airline", task_id)

    def test_renamed_schema_and_unknown_legacy_tool(self):
        env = make_environment("retail", True)
        self.assertTrue(all(tool.name.startswith("service_") for tool in env.get_tools()))
        before = env.get_db_hash()
        response = env.get_response(ToolCall(id="bad", name="cancel_pending_order", arguments={}))
        self.assertTrue(response.error)
        self.assertEqual(before, env.get_db_hash())
        messages = env.canonical_messages([AssistantMessage(role="assistant", tool_calls=[
            ToolCall(id="bad", name="cancel_pending_order", arguments={})])])
        self.assertEqual(messages[0].tool_calls[0].name, "unavailable_cancel_pending_order")

    def test_missing_argument_error_is_preserved(self):
        native = make_environment("retail", False)
        shifted = make_environment("retail", True)
        one = native.get_response(ToolCall(id="x", name="get_order_details", arguments={}))
        two = shifted.get_response(ToolCall(id="x", name="service_get_order_details", arguments={}))
        self.assertEqual(one.content, two.content)
        self.assertTrue(one.error and two.error)

    def test_all_development_reference_paths_preserve_state(self):
        manifest = json.loads((ROOT / "pilot_manifest.json").read_text())
        verified = 0
        for domain in ["retail", "airline"]:
            for task_id in manifest["domains"][domain]["development_ids"]:
                task = load_task(domain, task_id)
                baseline, shifted = make_environment(domain), make_environment(domain, True)
                initial = task.initial_state
                for env in [baseline, shifted]:
                    env.set_state(initial.initialization_data if initial else None,
                                  initial.initialization_actions if initial else None,
                                  initial.message_history or [] if initial else [])
                for i, action in enumerate(task.evaluation_criteria.actions or []):
                    original = ToolCall(id=str(i), name=action.name, arguments=action.arguments, requestor=action.requestor)
                    renamed = original.model_copy(deep=True)
                    if renamed.requestor == "assistant":
                        renamed.name = shifted.name_map[renamed.name]
                    a, b = baseline.get_response(original), shifted.get_response(renamed)
                    self.assertEqual(a.content, b.content, (domain, task_id, action.name))
                    self.assertEqual(a.error, b.error)
                    # Reference trajectories can intentionally contain a failed
                    # lookup followed by successful recovery (e.g. retail 37).
                    self.assertEqual(baseline.get_db_hash(), shifted.get_db_hash())
                verified += 1
        self.assertEqual(verified, 40)

    def test_retail_state_pass_does_not_imply_complete_success(self):
        task = load_task("retail", "13")
        env = make_environment("retail", True)
        messages = []
        for i, action in enumerate(task.evaluation_criteria.actions or []):
            call = ToolCall(id=str(i), name=env.name_map[action.name], arguments=action.arguments)
            messages.append(AssistantMessage(role="assistant", tool_calls=[call]))
            messages.append(env.get_response(call))
        grade = grade_deterministic("retail", task, env.canonical_messages(messages), "user_stop")
        self.assertTrue(grade["deterministic_pass"])
        self.assertIsNone(grade["native_success"])
        self.assertIn("NL_ASSERTION", grade["pending_components"])


if __name__ == "__main__":
    unittest.main()
