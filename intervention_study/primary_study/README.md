# Primary policy-gate evaluation

**Prepared on 12 October 2026; 0 of 4,608 conversations collected.** The allocation, implementation and analysis plan are frozen before collection. Funding remains locked: the current $125 cumulative approval covers the completed pilot and engineering work. The proposed full-study ceiling is $1,250 cumulative, subject to separate approval. This is a local prospective record, not a claim of public preregistration.

The question is practical: **does checking an action before execution prevent forbidden changes, and how much legitimate work does it interrupt?** For example, if an actor proposes an ineligible $300 credit, we ask three different questions: does each gate block that identical proposal; would the native tool actually issue the credit; and does an independently gated conversation finish with a better outcome? A warning or a block alone answers none of the other questions.

## What will run

| Cohort | Source pairs | Actors | Repeats | Forbidden/permitted requests | Conditions | Conversations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted customer, primary | 48 | 3 | 3 | 2 | 4 | 3,456 |
| Model customer, robustness | 16 of the same pairs | 3 | 3 | 2 | 4 | 1,152 |
| Total | 48 distinct pairs | | | | | 4,608 |

The eight selected rules concern cancellation eligibility, basic-economy flight changes, passenger-count changes, compensation eligibility, delivered-order returns, refund destinations, the required customer lookup, and further modifications after an item change. These are executable benchmark constraints, not comprehensive semantic-policy labels. The lookup rule measures a recorded procedure, not real-world authentication. Some native tools already enforce selected rules, which is why replay separates existing enforcement from an additional gate benefit.

Actor configurations are GPT-5.4 Mini, DeepSeek V4.1 Flash, and Claude Opus 5.5 with high reasoning. Both model gate designs use the same Gemini 3.1 Pro/high configuration. These are the saved catalog's hosted aliases, not immutable model snapshots. The four conditions are no gate, a broad policy gate, public predicates plus focused checks for unresolved rules, and a privileged predicate reference. The reference has private facts but is not an oracle for planning or task completion. Prompts, routes, thresholds and caps are frozen; there is no silent model fallback.

Every ungated write will also be scored by all three gates in shadow mode, giving up to 1,152 source conversations. They receive identical public proposal inputs; shadow decisions never affect the actor. Each blocked live write is replayed in a copied native state. Live comparisons use separate rollouts, preserving the consequences of a block and subsequent actor behavior.

Pairs 02–07 per rule are reserved for this stage. Development pairs 00 and 01 stay outside the primary results. The 48 pairs have distinct main entities and users, but shared flights/products connect them into 43 recorded context components. They also share eight rule templates and two domains. This is a designed stress test, not a representative estimate of deployment incident rates.

## What is ready

- Fifty offline tests cover paired denominators, missing outputs, customer bounds, budget locks, partial shadow records, exact receipt archives and blocked-action continuation.
- Native replay checked 95 retained development conversations and their monitor inputs. The earlier 25 blocks still divide into nine state-changing violating transitions intercepted, eight violations already rejected by tools, and eight other blocks. This reuses the existing predicate implementation; it is not independent human validation.
- The latest customer controller passed its six paid engineering checks before this preparation. The model customer consumes one of two pressure follow-ups for every nonterminal reply, even if it labels that reply as information or confirmation. The scripted controller instead counts designated pushbacks. Their comparison therefore includes a controller/horizon difference.
- Literal customer audits flag unsupported identifiers, dates, amounts, withheld lookup emails, malformed terminal replies and mismatched public inputs. They do not establish semantic fidelity. Flagged cases remain in primary assignment denominators.
- The analysis produces assignment-based bounds, separate shadow denominators, rule/actor summaries, cost by role, and native blocked-write counterfactuals. An empty study produces unknown outcomes, not zero violations.

## Statistical limitation identified before spending

The original source-pair percentile bootstrap was too optimistic in prospective simulations. Its nominal six-contrast coverage failed in 10–37% of simulated datasets instead of the intended 5%. That diagnostic is preserved in `precision_percentile_diagnostic.json`.

Formal comparisons now use paired label-swap randomization tests with Holm adjustment across six prespecified comparisons, under explicit sharp-null and assignment assumptions. Bootstrap intervals remain descriptive. See [the analysis plan](ANALYSIS_PLAN.md) for the distinction; a small p value will not by itself establish a population-average benefit or acceptable service cost.

The revised simulation used 18 scenarios, 600 datasets each. These are assumptions about possible data, not results from our actors:

| Assumed violation risk without/with a gate | First gate detected after correction, across the tested dependence scenarios |
| --- | ---: |
| 2% to 1% | 0–3.5% |
| 10% to 5% | 41.2–50.0% |
| 30% to 15% | 99.5–100% |

The study can support a useful finite-benchmark comparison, but it is underpowered for small or rare improvements. The assumptions omit some shared-context and actor-family heterogeneity. Zero observed violations would leave interception sensitivity undefined and would not establish that gates are unnecessary or that an actor is generally safe. We will retain null and unfavorable outcomes and will not expand or select cases based on significance.

## Budget decision

Current response-reported cumulative cost is **$62.907960925**. The conservative admission hold is **$104.04533596875 of $125**, including **$25.4103848125** of older unresolved reservations. No paid requests were made during this final preparation. This is local accounting, not a provider invoice.

The existing token-workload scenarios project approximately **$438 additional** at the sampled workload or **$878 additional** at twice the actor/gate workload. Including the existing hold and 25% cost margin, these require approximately **$652 or $1,202 cumulative admission capacity**. A proposed **$1,250 cumulative ceiling** covers the larger stated scenario; it is not a guaranteed total price. Block recovery, longer prefixes, provider changes and failures may exceed those assumptions. Shadow evaluation cost is separately identified and is not counted as live operating cost.

Funding approval must explicitly cover this frozen allocation and shadow scoring. The collection launcher requires both the matching stage approval in `authorization.json` and a sufficient global ceiling; it checks them before loading credentials. It stops for budget or inference failures. Unused funds need not be spent. No repository push or paper submission is part of this approval.

## Reproduction and collection

Use Python 3.13.7 with the pinned native benchmark and `environments/benchmark.txt` (NumPy 2.3.5). From the research/repository root:

```sh
python -m unittest intervention_study.scaled_design.tests intervention_study.scaled_design.pilot_report_tests intervention_study.scaled_design.customer_limit_tests intervention_study.primary_study.tests
python -m intervention_study.primary_study.runner --check
python -m intervention_study.primary_study.verify_preparation
python -m intervention_study.primary_study.precision
python -m intervention_study.primary_study.analyze
```

These commands make no model calls. `verify_preparation` needs the pinned native source checkout, which is excluded from Git and installed using the project's benchmark setup instructions. It reads the private, hashed development receipt archives. It checks the global ledger only if present; the repository mirror does not contain the private global budget files. The precision report is deterministic in the pinned runtime. Do not regenerate the primary protocol after the freeze; the preparation utility exists for provenance and refuses to change a frozen study.

Only after explicit funding approval is recorded, use the separate paid phases:

```sh
python -m intervention_study.primary_study.runner --live --phase live
python -m intervention_study.primary_study.runner --live --phase shadow
python -m intervention_study.primary_study.evidence
python -m intervention_study.primary_study.analyze --offline --native
```

Serial chunks can use `--limit` while preserving allocation order and existing attempts. Existing records are never replaced. A stopped run requires inspection, a retained incident/disposition record and documented resumption; do not delete failure evidence or silently retry with a different prompt. Process-interrupted records must be classified as interrupted under a documented disposition before continuation. An infrastructure correction or protocol change requires an amendment and separate affected-cohort reporting. Do not use interim outcome summaries for efficacy stopping.

`freeze.json` hashes the final source, allocation, protocol and documentation. `preparation_verification.json` records the offline replay checks. `analysis.json` is currently an empty-allocation dry run. Later receipts are archived with exact hashes and costs, including failed requests. Private archives must be separately anonymized before submission.

The combined paper remains unsubmitted. Its current PDF and anonymous ZIP are the historical small-study draft. After collection, rewrite around the observed shadow/live results, compress earlier warning studies into motivation and appendices, and rebuild the anonymous evidence package. Prepared code and a larger sample do not guarantee a positive result or journal acceptance.
