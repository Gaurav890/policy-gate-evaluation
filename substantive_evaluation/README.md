# Substantive-rule evaluation extension

This folder contains the fixed 96-conversation exploratory extension and matched-input monitoring experiment. It is separate from the earlier 24-run pilot and the three reserved-test cohorts. The current supplement includes this extension; see the root README for the complete reproduction workflow.

Read `report.md` first. `protocol.json`, `collection_freeze.json`, `monitor_protocol.json`, `monitor_freeze.json` and `analysis_freeze.json` record the task allocation, original code hashes, requested targets and analysis. Four scheduling shards collected the fixed cells; monitoring used nonoverlapping scheduling shards and a final coverage pass. Scheduling did not change task selection, prompts, thresholds or retained failures.

The monitor evaluates the same public input under three targets and two models. It receives no labels, private customer instructions, later tool results or final grades. A second implementation checks six literal predicates against raw public prefixes. This is not human semantic review. All contextual and policy–tool ambiguities remain explicitly limited.

## Offline reproduction

Run from the project root with Python 3.13 after installing `study/analysis_requirements.txt`:

```sh
python3 -m unittest substantive_evaluation.test_evaluation substantive_audit.test_audit
python3 substantive_evaluation/verify_labels.py
python3 substantive_evaluation/analyze.py
python3 -m substantive_evaluation.dependence
python3 substantive_evaluation/dependency_inventory.py
python3 substantive_evaluation/strata.py
python3 substantive_evaluation/build_report.py
python3 substantive_evaluation/verify_release.py
```

These commands do not make paid model calls. Collection/scoring commands require `--live`; do not delete result files to force a new realization. The hosted aliases and unseeded customer/actor responses are not exactly regenerable; saved-input analyses are reproducible.

`labels.json` holds all checked constraints and their visible evidence indices. `matched_points.json` holds matched prefix hashes and scores. `episode_results.json`, `sampled_timing.json`, `strata.json` and `entity_sensitivity.json` keep different estimands separate. `verification.json` audits fixed-cell coverage. `spending.json` is local response-reported accounting, not an invoice.

`paper/expanded_review_draft.tex` and `output/pdf/expanded-review-draft.pdf` are the expanded anonymous draft. `paper/main.tex` is historical. The current package uses `paper/expanded_review_draft.tex`. No submission has been made. The draft is not a claim of acceptance or completed human adjudication.
