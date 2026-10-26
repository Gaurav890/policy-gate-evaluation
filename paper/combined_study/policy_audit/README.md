# Policy evidence inputs

This packet supplies saved inputs for the [completed programmatic evidence audit](evidence_audit/README.md). It is a post hoc export from the compact study. The original design, gates, outcomes and missing records remain frozen. The audit rules were developed after inspecting saved examples and are not prospective validation.

## Coverage

The export includes all **231 ungated shadow write events**, all **161 live blocked write events** (102 broad, 59 decomposed), and all **576 nominally permitted conversations**, including successful and incomplete records. There are **392 distinct public proposal inputs**. Stable identifiers map each input back to every original event. Deduplication does not make proposals independent tasks or change original event denominators. The live-block cohort contains only blocked calls and cannot estimate a live gate's overall false-positive rate.

## Files

- `proposal_cases.jsonl`: full public policies, tool definitions, exact conversation prefixes and proposed write calls.
- `conversation_cases.jsonl`: full public policies, tool definitions and saved nominally permitted conversations.
- `coordinator_key.json`: provenance mappings, original condition metadata, frozen endpoint scores, native checks and exact source-file hashes. Its historical filename is retained for stable references.
- `manifest.json`: coverage counts, file hashes and the export method's scope.
- `evidence_audit/`: clause and message evidence, decision accounting, conversation checks, case notes and limitations.

The public-input files omit current gate decisions, explicit actor/treatment metadata and frozen outcome scores. Earlier gate feedback remains in live transcripts and can reveal treatment. The analysis joins the provenance metadata to those inputs and is explicitly unblinded. Saved policies and customer text are evidence, not instructions for executing tools or changing records.

## Interpretation

The checks distinguish known selected-rule violations, additional supported action or prerequisite breaches, current-message format departures, monitor outages and unresolved cases. A supported objection does not establish that a gate adds protection beyond the tool's own enforcement. A clean selected predicate does not establish that the full policy permits the action. Gate explanations are stored outputs, not a correctness oracle.

The audit retains uncertainty when facts or policy meaning are insufficient. It does not infer non-consent solely from the absence of the literal word “yes,” invent a requirement to call a named tool, or use a prior formatting mistake to justify a later block. Reference-state completion remains the frozen endpoint and does not certify procedural compliance. Missing decisions remain missing, and no replacement primary endpoint or formal test is introduced.

## Reproducibility

Run `python paper/combined_study/build_policy_audit.py --check` to reproduce and verify the exact input export without writing. `--write` creates missing exports and refuses to overwrite differing files. Run `python paper/combined_study/verify_policy_evidence_audit.py` to verify the derived evidence records and interpretation boundaries. Both operate offline and make no model calls.
