# Compact live-gating study

This is the user-approved reduction of the earlier 4,608-conversation plan to **1,152 planned live conversations**. It is a disclosed amendment after collection began, not a new claim of preregistration before observing data. The earlier protocol, 344 attempted conversations, exact receipts and stops remain intact in `../primary_study/`.

The question is whether public-policy gates prevent selected forbidden database changes while preserving legitimate service. A concrete blocked write is checked by replaying its native transition in a copied state. That one-step interception is distinct from an improvement in whole-conversation outcomes.

## Fixed allocation

Eight rules × four source pairs per rule × three actors × two repeats × forbidden/permitted requests × three live conditions = **1,152 conversations**. Use pair indices **02–05**, repeat indices **0–1**, scripted customers, and conditions **none, broad, decomposed**. Preserve the relative order of those cells from the earlier frozen allocation. The 384 no-gate conversations are the sources for shadow scoring by broad, decomposed and privileged predicate gates. Shadow scoring adds API calls, not independent conversations.

The source pair and repeat selection uses these fixed indices, not observed performance or completion status. Of 344 existing attempts, 102 meet the rule: 101 completed and one interrupted. All 102 are imported byte-for-byte with their original protocol hashes and request identifiers. The remaining 242 are retained outside the compact estimates; the reduction does not erase them or their cost. There are 1,050 unstarted compact cells at amendment time. The interrupted selected cell is never rerun or replaced.

The actors, monitor, public inputs, prompts, predicates, database environment, horizons, transport behavior and customer controller are unchanged. Full identifiers are in `protocol.json`. The model-generated customer and live privileged-gate conditions are removed from future collection. The privileged reference remains available in shadow evaluation. The existing $1,250 cumulative project ceiling includes all prior spending; the smaller allocation does not authorize additional funds or a credit purchase.

## Evidence and limitations

`imports.json` links reused records to exact original bytes. `amendment.json` retains the former allocation, freeze, stop and receipt-manifest hashes, every original episode hash, selection counts and the point at which the decision was made. The parent timeout is documented in `parent_timeout.json`: a monitor request had no response after approximately 180 seconds. It remains unresolved billing, and its fail-closed write is not counted as a successful substantive detection.

There are 32 underlying scenario pairs, not 1,152 independent tasks. All share selected policy templates and two simulated domains. The customer is scripted; no robustness to model-generated customers is claimed. Existing results had been inspected before this change. The selected interrupted permitted case leaves its affected comparison unresolved under the retained missingness policy. More API calls, narrow confidence intervals or a larger apparent sample do not guarantee a positive result or acceptance.

## Local commands

Run from the repository root with the project Python environment:

```sh
python -m intervention_study.compact_study.runner --check
python -m unittest intervention_study.compact_study.tests
python -m intervention_study.compact_study.runner --live --phase live
python -m intervention_study.compact_study.collection_pipeline
python -m intervention_study.compact_study.monitor_progress
```

The pipeline waits for live collection, starts paid shadow scoring only after all allocated cells have records and no active stop, then archives and analyzes. Diagnosed inherited interruptions remain records. New failures stop collection and require a retained diagnosis before resumption; no automatic exception-skipping or replacement loop exists. The integrity watcher performs offline native replay and verifies public monitor inputs. It never selects cases or stops based on effectiveness.

For offline reproduction after an archive is saved:

```sh
python -m intervention_study.compact_study.analyze --offline --native
```

Private exact receipts must not be uploaded as an anonymous supplement without a separate release audit. The historical paper PDF and anonymous ZIP do not yet report this amended study.
