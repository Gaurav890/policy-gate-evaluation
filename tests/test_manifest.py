"""Guard task separation and allocation reproducibility using artificial IDs."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_manifest import allocate


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [{"id": str(i)} for i in range(40)]
        self.splits = {"train": [str(i) for i in range(30)],
                       "test": [str(i) for i in range(30, 40)],
                       "base": [str(i) for i in range(40)]}

    def test_order_invariance_and_partition(self):
        first = allocate(self.tasks, self.splits, "retail")
        reverse = {key: list(reversed(value)) for key, value in self.splits.items()}
        self.assertEqual(first, allocate(list(reversed(self.tasks)), reverse, "retail"))
        development = set(first["development_ids"])
        remaining = set(first["unallocated_training_ids"])
        reserved = set(first["reserved_upstream_test_ids"])
        self.assertEqual(len(development), 20)
        self.assertFalse(development & reserved)
        self.assertFalse(development & remaining)
        self.assertEqual(development | remaining | reserved, set(self.splits["base"]))
        self.assertTrue(set(first["smoke_ids"]) <= development)

    def test_rejects_test_leakage(self):
        self.splits["train"].append("30")
        with self.assertRaises(ValueError):
            allocate(self.tasks, self.splits, "retail")

    def test_rejects_duplicate_tasks(self):
        self.tasks.append(self.tasks[0])
        with self.assertRaises(ValueError):
            allocate(self.tasks, self.splits, "airline")

    def test_rejects_unknown_split_member(self):
        self.splits["test"].append("missing")
        with self.assertRaises(ValueError):
            allocate(self.tasks, self.splits, "airline")

    def test_rejects_duplicate_split_member(self):
        self.splits["train"].append("0")
        with self.assertRaises(ValueError):
            allocate(self.tasks, self.splits, "airline")

    def test_rejects_oversized_pilot(self):
        with self.assertRaises(ValueError):
            allocate(self.tasks, self.splits, "airline", count=31)


if __name__ == "__main__":
    unittest.main()
