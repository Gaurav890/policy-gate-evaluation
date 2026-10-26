# Live gating: 64 attempts, eight source pairs

The manuscript now includes this exploratory follow-up. GPT-5.4 Mini generated its replies and actions; a scripted customer supplied fixed facts and at most two pressure replies. Each of eight rules has one forbidden and one permitted request, run once in each of four gate conditions. All 32 pressure conversations completed; 29 of 32 controls completed.

See `analysis.json`, the regenerated `RESULTS.md`, and `release/live_gating_ledger.json` at the package root. The latter links the paper table and $300-credit example to source hashes. `verification.json` preserves 64 native replays, 58 independent write-label checks and 27 public-input checks. `blocked_write_audit.json` preserves the post-collection one-step diagnostic on all 25 blocked proposals.

From the extracted package root:

```sh
python3 release/unpack_records.py
python3 release/live_gating.py
```

This verifies anonymized receipts and recomputes the saved-record analysis; it checks the saved native results but does not rerun the simulator. With the pinned native simulator installed, independently rerun its transitions and the offline tests:

```sh
python3 release/live_gating.py --native
python3 -m unittest intervention_study.live_gating.tests
```

No API calls are made by these commands. Use Python 3.13 for byte-identical cost aggregation. Scientific source freezes stay unchanged. The adapter substitutes only the receipt reader, retaining the transformation ledger between private original hashes and released hashes.

The frozen generated `RESULTS.md` retains the collection-time statement that the then-existing paper was historical. This README and the current manuscript supersede that document-status statement; the recorded results and protocol remain unchanged. No larger frontier-actor study has been collected as part of this comparison.
