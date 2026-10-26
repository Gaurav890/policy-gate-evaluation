"""Run a bounded native benchmark development batch; never final-test tasks."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from unittest.mock import patch

from gateway_budget import ROOT, Budget, BudgetExceeded, Gateway, MODELS, write_json
from benchmark_adapter import bridge_generate, grade_deterministic, load_task, make_environment
from prepare_manifest import build_manifest
from tau2.agent.llm_agent import LLMAgent
from tau2.user.user_simulator import UserSimulator
from tau2.orchestrator.orchestrator import Orchestrator


def run_episode(gateway, domain, task_id, actor, shifted, output_dir):
    condition = "rename" if shifted else "baseline"
    episode = f"{domain}-{task_id}-{actor}-{condition}"
    path = output_dir / (episode + ".json")
    if path.exists():
        print(json.dumps({"episode": episode, "status": "already_recorded"}), flush=True)
        return
    task = load_task(domain, task_id)
    if task.initial_state and task.initial_state.message_history:
        raise ValueError("Initial-history tasks require an additional audited mapping; not supported in this batch")
    env = make_environment(domain, shifted)
    agent = LLMAgent(tools=env.get_tools(), domain_policy=env.get_policy(), llm=actor, llm_args={})
    user = UserSimulator(llm="claude", instructions=str(task.user_scenario), tools=None, llm_args={})
    orchestrator = Orchestrator(domain=domain, agent=agent, user=user, environment=env, task=task,
                                max_steps=60, max_errors=10, seed=None, timeout=900,
                                simulation_id=episode)
    result = {"episode": episode, "domain": domain, "task_id": task_id, "actor": actor,
              "condition": condition, "repeat": 0, "task_group": f"{domain}:{task_id}",
              "status": "started", "policy": env.policy,
              "tools": [tool.openai_schema for tool in env.get_tools()], "name_map": env.name_map,
              "max_steps": 60, "seed": None,
              "note": "Hosted sampling is not seed-pinned; paired tasks, not identical stochastic trajectories."}
    write_json(path, result)
    start = time.monotonic()
    generate = bridge_generate(gateway, episode)
    try:
        with patch("tau2.agent.llm_agent.generate", generate), patch("tau2.user.user_simulator.generate", generate):
            simulation = orchestrator.run()
        canonical = env.canonical_messages(simulation.messages)
        result["grading"] = grade_deterministic(domain, task, canonical, simulation.termination_reason.value)
        result["simulation"] = simulation.model_dump(mode="json")
        result["canonical_messages"] = [message.model_dump(mode="json") for message in canonical]
        result["live_db_hash"] = env.get_db_hash()
        result["status"] = "completed"
    except Exception as exc:
        result["status"] = "incomplete"
        result["error_type"] = type(exc).__name__
        result["partial_messages"] = [message.model_dump(mode="json") for message in orchestrator.get_messages()]
        result["elapsed_s"] = time.monotonic() - start
        write_json(path, result)
        raise
    result["elapsed_s"] = time.monotonic() - start
    write_json(path, result)
    print(json.dumps({"episode": episode, "status": result["status"],
                      "deterministic_pass": result["grading"]["deterministic_pass"],
                      "native_success": result["grading"]["native_success"],
                      "messages": len(result["simulation"]["messages"]),
                      "reserved_usd": round(gateway.budget.total_reserved(), 4)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--actors", nargs="+", choices=["claude", "deepseek"], default=["claude"])
    parser.add_argument("--tasks-per-domain", type=int, default=2)
    parser.add_argument("--ceiling", type=float, default=22.0)
    parser.add_argument("--out", type=Path, default=ROOT / "groundwork" / "development-v001")
    args = parser.parse_args()
    if not args.live:
        raise SystemExit("Paid execution requires --live and the recorded study authorization")
    if not 1 <= args.tasks_per_domain <= 20:
        raise SystemExit("tasks-per-domain must be between 1 and 20")
    actual = build_manifest(ROOT / "groundwork/benchmark-source")
    saved = json.loads((ROOT / "pilot_manifest.json").read_text())
    if actual != saved:
        raise SystemExit("Benchmark provenance differs from prepared manifest")
    args.out.mkdir(parents=True, exist_ok=True)
    source_hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                     for name in ["gateway_budget.py", "benchmark_adapter.py", "run_development.py"]}
    freeze = {"source_sha256": source_hashes, "models": MODELS, "benchmark_revision": actual["benchmark_revision"],
              "conditions": ["baseline", "rename"], "rename_rule": "service_ prefix on every assistant tool",
              "customer": "claude", "max_steps": 60, "repeat": 0,
              "outcome_scope": "deterministic native reward components; retail NL checks pending",
              "task_allocation": "first N preselected development tasks per domain",
              "execution_order": "task position, domain, actor; condition order alternates by position/domain/model"}
    freeze_path = args.out / "freeze.json"
    if freeze_path.exists() and json.loads(freeze_path.read_text()) != freeze:
        raise SystemExit("Code/config changed; use a new development output directory")
    write_json(freeze_path, freeze)
    gateway = Gateway(Budget(ceiling=args.ceiling))
    for position in range(args.tasks_per_domain):
        for domain_index, domain in enumerate(["retail", "airline"]):
            task_id = saved["domains"][domain]["development_ids"][position]
            for actor in args.actors:
                actor_index = ["claude", "deepseek"].index(actor)
                conditions = [False, True] if (position + domain_index + actor_index) % 2 == 0 else [True, False]
                for shifted in conditions:
                    run_episode(gateway, domain, task_id, actor, shifted, args.out)


if __name__ == "__main__":
    main()
