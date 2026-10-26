#!/bin/sh
set -eu
# Run from the extracted supplement. No API key or model call is used.
python3 release/verify_inventory.py
python3 release/unpack_records.py
python3 study/analyze_confirmatory.py --final
python3 study/analyze_ablation.py
python3 study/build_paper_artifacts.py
python3 study/verify_artifact.py
python3 extension/analyze.py --final
python3 extension/verify.py
python3 extension/sensitivity.py
python3 extension/build_report.py
python3 replication/analyze.py --final
python3 replication/verify.py --final
python3 replication/failure_audit.py
python3 replication/build_report.py
python3 -m unittest substantive_evaluation.test_evaluation substantive_audit.test_audit
python3 substantive_evaluation/verify_labels.py
python3 substantive_evaluation/analyze.py
python3 -m substantive_evaluation.dependence
python3 substantive_evaluation/dependency_inventory.py
python3 substantive_evaluation/strata.py
python3 substantive_evaluation/build_report.py
python3 substantive_evaluation/plot.py
python3 substantive_evaluation/verify_release.py
python3 release/verify_receipts.py
python3 release/examples.py
python3 release/live_gating.py
python3 substantive_evaluation/make_draft.py
if command -v tectonic >/dev/null 2>&1; then
  tectonic paper/expanded_review_draft.tex --outdir paper --keep-logs
elif command -v latexmk >/dev/null 2>&1; then
  (cd paper && latexmk -pdf -interaction=nonstopmode expanded_review_draft.tex)
else
  printf '%s\n' 'Analysis complete. Install Tectonic or latexmk to compile paper/expanded_review_draft.tex.'
fi
