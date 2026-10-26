"""Prepare development task allocation; never execute benchmark or model code."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


REVISION = "b7ea9074c1cba482b30687fecdb5c8425fd6f619"
SEED = "tool-shift-development-v1"


def allocate(tasks, splits, domain, count=20):
    """Choose development tasks by stable hash, preserving upstream test IDs."""
    if count < 2:
        raise ValueError("At least two development tasks are required")
    ids = [str(task["id"]) for task in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate task IDs")
    normalized = {}
    for name in ("train", "test", "base"):
        members = [str(value) for value in splits[name]]
        if len(set(members)) != len(members):
            raise ValueError("Duplicate split membership")
        normalized[name] = set(members)
    train, test, base = (normalized[name] for name in ("train", "test", "base"))
    if train & test or train | test != base or base != set(ids):
        raise ValueError("Task coverage or train/test separation is invalid")
    if len(train) < count:
        raise ValueError("Insufficient upstream training tasks")
    ranked = sorted(train, key=lambda task_id: hashlib.sha256(
        f"{SEED}:{domain}:{task_id}".encode()).hexdigest())
    return {
        "task_count": len(ids),
        "upstream_train_count": len(train),
        "upstream_test_count": len(test),
        "development_ids": ranked[:count],
        "smoke_ids": ranked[:2],
        "unallocated_training_ids": sorted(train - set(ranked[:count])),
        "reserved_upstream_test_ids": sorted(test),
        "grouping_status": "task IDs only; task-family audit pending",
    }


def build_manifest(root):
    """Validate the checkout and produce deterministic task and source metadata."""
    def git(*args):
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True).strip()

    revision = git("rev-parse", "HEAD")
    if revision != REVISION:
        raise ValueError(f"Expected {REVISION}, found {revision}")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Benchmark has modified tracked files")
    domains = {}
    hashes = {}
    paths = [root / name for name in ("pyproject.toml", "uv.lock", "LICENSE")]
    for domain in ("retail", "airline"):
        directory = root / "data" / "tau2" / "domains" / domain
        tasks = json.loads((directory / "tasks.json").read_text())
        splits = json.loads((directory / "split_tasks.json").read_text())
        domains[domain] = allocate(tasks, splits, domain)
        paths.extend(directory / name for name in (
            "tasks.json", "split_tasks.json", "policy.md", "db.json"))
        paths.extend(sorted((root / "src" / "tau2" / "domains" / domain).glob("*.py")))
    for path in sorted(paths):
        hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    plans = []
    for stage, key, models, shifts in (
        ("smoke", "smoke_ids", 1, ["baseline", "tool_name_rename"]),
        ("pilot", "development_ids", 2, ["baseline", "tool_name_rename"]),
    ):
        episodes = []
        for domain, allocation in domains.items():
            for task_id in allocation[key]:
                for model in range(1, models + 1):
                    for shift in shifts:
                        episodes.append({
                            "domain": domain,
                            "task_id": task_id,
                            "task_group": f"{domain}:{task_id}",
                            "model_slot": f"actor_{model}",
                            "condition": shift,
                            "repeat": 0,
                        })
        plans.append({"stage": stage, "actor_episode_count": len(episodes),
                      "episodes": episodes})
    return {
        "schema_version": 1,
        "status": "development_plan_not_experimental_results",
        "benchmark_repository": "https://github.com/sierra-research/tau2-bench",
        "benchmark_revision": revision,
        "benchmark_python_requirement": ">=3.12,<3.14",
        "selection_seed": SEED,
        "selection_uses_outcomes": False,
        "source_sha256": hashes,
        "domains": domains,
        "budget_usd": None,
        "live_execution_enabled": False,
        "model_configuration": None,
        "plans": plans,
        "notes": [
            "Smoke tasks are a subset of pilot tasks, not an independent dataset.",
            "Counts exclude user-simulator/judge calls and adaptation collection.",
            "Reserved upstream test tasks must not be used for development.",
            "Unallocated training tasks are not a finalized calibration split.",
            "Source hashes cover domain inputs/code and environment metadata; the revision pins the remaining tracked source.",
        ],
    }


def main():
    """Write a new manifest, refusing to overwrite an existing artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    manifest = build_manifest(args.benchmark.resolve())
    with args.out.open("x") as output:
        json.dump(manifest, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps({plan["stage"]: plan["actor_episode_count"]
                      for plan in manifest["plans"]}, sort_keys=True))


if __name__ == "__main__":
    main()
