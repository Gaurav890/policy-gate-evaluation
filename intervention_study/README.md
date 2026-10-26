# Preparation and live-gating evidence

This directory preserves the development of the eight-rule intervention study. It is separate from the earlier reserved-task and matched-input cohorts. Read `live_gating/README.md` for the 64-attempt comparison added to the manuscript.

The versioned freezes, all recorded preparation attempts, fixture outputs, case definitions and validation ledgers are retained. Earlier diagnostic collection failures and stopping-rule amendments are not confirmatory data. Preparation contains 632 API records and the live comparison another 384. They are anonymized in separate archives under `release/`; the original raw-byte manifests remain audit commitments.

Run `python3 release/live_gating.py` from the package root after `python3 release/unpack_records.py`. This verifies all 1,016 additional receipts, the frozen source dependencies, saved native-replay evidence, public gate inputs and scores, then reproduces the live analysis and paper table. It makes no model calls. Original evidence readers refer to private byte-exact archives; use the release adapter for this anonymous distribution. It explicitly checks original-to-released hash mappings rather than claiming the anonymized bytes equal the private originals.

The original preparation report and cost checkpoints are historical; their full-study budget proposals are not completed experiments or current authorization. No further collection is part of this release. The software labels cover eight literal constraints, not all semantic policies, and no human review responses are used.
