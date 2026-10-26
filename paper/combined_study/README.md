# Current combined manuscript

**From Warnings to Interventions: Evaluating Policy Enforcement in Tool-Using LLM Agents** is organized around warning detection, added transition protection and subsequent task outcomes. The current master is `manuscript_source.md`; generated text is `manuscript_draft.md`, and the complete PDF is `manuscript.pdf`. Shared earlier sections remain editable in `../editorial/`, including `replication.tex`. That file is a section fragment; compile the parent manuscript for a complete PDF.

The verified PDF has 39 pages; the main text ends on page 12, followed by references and 14 appendices. It has five figures and 28 captioned tables. The revision preserves 55 references, all original outcomes, nine incomplete live records, one missing-output shadow source, 65 unresolved live blocks and four withheld original formal comparisons. It adds explicitly unplanned Mini-specific paired tests and a matched completion-loss recount, not new collection. The 65 unresolved blocks remain a limitation; no human validation results are claimed.

## Reproduce

The clean principal-result environment uses Python 3.13.7, NumPy 2.3.5 and Pandoc 3.8.3. The public artifact includes a pinned Dockerfile and dependency file. Run from the artifact root:

```sh
python paper/combined_study/reproduce_principal.py
```

This rechecks the compact records, receipts, frozen sources, programmatic audit, paired exports and exploratory tests, and regenerates manuscript sources. Earlier main-text tables are rederived from saved episodes and monitor scores. The reproduction report records precisely which checks ran. No credentials, network access or inference calls are required during execution.

`exploratory_actor_tests.csv` contains nominal and cluster-sensitivity p-values. `completion_loss_cases.csv` lists all observed losses and their blocks. `policy_audit/independent_annotation/` contains the fixed rubric, 95 cases, blank forms and agreement script. Keep its coordinator key and the rest of the evidence archive separate from annotators until their independent forms are locked.

## Build the PDF

Use Pandoc 3.8.3, the pinned plotting environment recorded with the artifact and Tectonic 0.17. Keep the unchanged official TMLR style, earlier source fragments and figure files present.

```sh
python paper/combined_study/build_exploratory_followup.py
python paper/combined_study/build_principal_tables.py
python paper/combined_study/build_manuscript.py
python paper/combined_study/figures/build_evaluation_flow.py
tectonic -X compile paper/combined_study/figures/assignment_bounds.tex
tectonic -X compile paper/combined_study/manuscript.tex --keep-logs
```

`manuscript_verification.json` records the latest full-project compile, evidence checks and visual review. `citation_audit_2026.md` records public primary-source checks for the nine works dated 2026. `revision_plan.md` separates completed work from outstanding evidence. `confirmatory_plan.md` remains a prospective draft, not a registration or spending authorization.

## Distribution

This copy is distributed in the public [Policy Gate Evaluation repository](https://github.com/Gaurav890/policy-gate-evaluation). Frozen observations are unchanged; the current revision clarifies definitions, references and evidentiary limits. See [public release provenance](../../docs/RELEASE.md) for privacy transformations, verification scope and the relationship to historical review-package records. Publication on GitHub does not imply journal submission or acceptance.

The [browser review form](../../review/README.md) delivers the original 95 cases plus four supplementary completion-loss cases. Responses stay private and are not included in this artifact.
