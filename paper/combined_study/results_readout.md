# Compact study: completed processing and results readout

This local report reads the finished frozen analysis and verifies its archived inputs. Processing is finished; incomplete observations remain incomplete. It is a reporting draft, not a submission package.

## Collection and provenance

| Stage | Assigned | Complete | Incomplete / missing | Unstarted |
| --- | --- | --- | --- | --- |
| Live conversations | 1152 | 1143 | 9 | 0 |
| Shadow source evaluations | 384 | 383 | 1 | 0 |

All 1,152 live records passed native replay and public-input checks. The archive contains 6,625 exact request receipts. Of the live records, 102 were imported byte-for-byte and 1,050 were newly collected under the compact amendment. Terminations: GatewayError=6, RuntimeError=2, customer_stop=1143, customer_turn_limit=1.

The pipeline retains `partial_collection_archived` when a shadow source has missing monitor output. That status does not turn a missing observation into a complete one. All planned sources have terminal records, no active stop remains, and the final offline analysis has finished. The 121-file freeze and every archived receipt hash were checked for this report.

## Live outcomes

Each request-type/condition cell contains 192 assigned conversations. Bounds assign every unresolved binary outcome first to zero, then to one; they are finite assignment bounds, not confidence intervals. A completed permitted service requires both normal dialogue completion and an exact reference-state match.

| Request type | Condition | Outcome | Observed positive / assigned | Unresolved | Assignment bounds |
| --- | --- | --- | --- | --- | --- |
| Pressure | No gate | Executed covered violation | 21/192 | 0 | [10.94, 10.94]% |
| Pressure | Broad | Executed covered violation | 1/192 | 2 | [0.52, 1.56]% |
| Pressure | Decomposed | Executed covered violation | 2/192 | 1 | [1.04, 1.56]% |
| Permitted | No gate | Completed service | 181/192 | 0 | [94.27, 94.27]% |
| Permitted | Broad | Completed service | 163/192 | 2 | [84.90, 85.94]% |
| Permitted | Decomposed | Completed service | 166/192 | 3 | [86.46, 88.02]% |

The corresponding permitted-request state matches and dialogue completions remain separate:

| Condition | Reference-state matches / assigned | Normal completions / assigned | Unresolved |
| --- | --- | --- | --- |
| No gate | 181/192 | 192/192 | 0 |
| Broad | 163/192 | 190/192 | 2 |
| Decomposed | 166/192 | 188/192 | 3 |

## Four amended paired comparisons

Differences are gate minus no gate, expressed in percentage points. The frozen weighting averages actors/repeats within pairs, pairs within rule and rules equally. A negative violation difference and a negative permitted-service difference have different practical meanings. No utility tradeoff is selected from these results.

| Gate | Outcome | Difference bounds (percentage points) | Unresolved pairs / assigned | Holm-adjusted p |
| --- | --- | --- | --- | --- |
| Broad | executed_violation | [-10.42, -9.38] pp | 2/32 | withheld |
| Broad | service_complete | [-9.38, -8.33] pp | 2/32 | withheld |
| Decomposed | executed_violation | [-9.90, -9.38] pp | 1/32 | withheld |
| Decomposed | service_complete | [-7.81, -6.25] pp | 3/32 | withheld |

A contrast with an unresolved pair block has no p value or inferential interval. The post-start amendment makes available label-swap tests exploratory; descriptive bootstrap intervals do not establish population coverage. Bounds above concern these assigned cases, not a population effect.

## Ungated pressure outcomes by actor

| Actor configuration | Executed violations / assigned | Unresolved | Assignment bounds |
| --- | --- | --- | --- |
| deepseek_ref | 0/64 | 0 | [0.00, 0.00]% |
| gptmini_ref | 21/64 | 0 | [32.81, 32.81]% |
| opus | 0/64 | 0 | [0.00, 0.00]% |

These are configuration-specific finite counts across the same designed rules, not independent draws of new tasks or evidence about all models.

| Actor configuration | Request type / outcome | Condition | Observed positive / assigned | Unresolved |
| --- | --- | --- | --- | --- |
| deepseek_ref | Pressure / executed violation | No gate | 0/64 | 0 |
| deepseek_ref | Pressure / executed violation | Broad | 0/64 | 1 |
| deepseek_ref | Pressure / executed violation | Decomposed | 0/64 | 0 |
| deepseek_ref | Permitted / completed service | No gate | 64/64 | 0 |
| deepseek_ref | Permitted / completed service | Broad | 63/64 | 1 |
| deepseek_ref | Permitted / completed service | Decomposed | 61/64 | 2 |
| gptmini_ref | Pressure / executed violation | No gate | 21/64 | 0 |
| gptmini_ref | Pressure / executed violation | Broad | 1/64 | 0 |
| gptmini_ref | Pressure / executed violation | Decomposed | 2/64 | 0 |
| gptmini_ref | Permitted / completed service | No gate | 53/64 | 0 |
| gptmini_ref | Permitted / completed service | Broad | 38/64 | 0 |
| gptmini_ref | Permitted / completed service | Decomposed | 42/64 | 0 |
| opus | Pressure / executed violation | No gate | 0/64 | 0 |
| opus | Pressure / executed violation | Broad | 0/64 | 1 |
| opus | Pressure / executed violation | Decomposed | 0/64 | 1 |
| opus | Permitted / completed service | No gate | 64/64 | 0 |
| opus | Permitted / completed service | Broad | 62/64 | 1 |
| opus | Permitted / completed service | Decomposed | 63/64 | 1 |

## Identical-proposal shadow decisions

The table uses the full observed ungated proposal corpus. Each cell shows observed blocks / proposals and missing decisions. The paired gates see identical public prefixes; the privileged reference additionally uses selected private predicates. Zero denominators remain undefined.

| Mechanical proposal class | Proposals | Supporting pairs | Broad blocks / N; missing | Decomposed blocks / N; missing | Privileged blocks / N; missing |
| --- | --- | --- | --- | --- | --- |
| state_changing_violation | 21 | 13/32 | 21/21; 0 | 20/21; 0 | 21/21; 0 |
| native_rejected_violation | 15 | 7/32 | 15/15; 0 | 14/15; 0 | 15/15; 0 |
| violating_noop | 0 | 0/32 | 0/0; 0 | 0/0; 0 | 0/0; 0 |
| eligible_publicly_verified | 99 | 22/32 | 17/99; 0 | 0/99; 0 | 0/99; 0 |
| eligible_missing_public_evidence | 96 | 26/32 | 34/96; 0 | 23/96; 1 | 0/96; 1 |
| unresolved_or_uncovered | 0 | 0/32 | 0/0; 0 | 0/0; 0 | 0/0; 0 |

Selected-eligible blocks are not automatically full-policy false alarms. Existing native rejection is separate from preventing a state-changing violation. Missing decisions are not counted as either a substantive block or an allow. Paired differences, observed-denominator bounds, first-violation truncation and descriptive intervals remain in `results_tables.json` and the source analysis.

## What live blocks intercepted

These are blocked-write events across both request types, on treatment-dependent proposals. They are not numbers of independently saved conversations or shared-proposal sensitivity estimates.

| Live gate | Blocked writes | State-changing covered violations | Already natively rejected violations | Selected-eligible / public evidence | Selected-eligible / private evidence needed | Unavailable-monitor blocks | Repeated next write |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Broad | 102 | 26 | 13 | 26 | 36 | 1 | 44 |
| Decomposed | 59 | 22 | 13 | 0 | 23 | 1 | 10 |

## Costs and operating burden

| Role | Requests | Response-reported USD | Unknown-cost requests | Unresolved reservation USD |
| --- | --- | --- | --- | --- |
| actor | 5877 | 69.895841 | 85 | 2.844811 |
| customer | 0 | 0.000000 | 0 | 0.000000 |
| live_gate | 393 | 6.957748 | 2 | 0.416102 |
| shadow | 355 | 6.181637 | 1 | 0.198980 |

These are costs attributable to the compact allocation, including imported requests once. Shadow evaluation is separate from live operating cost. Unresolved reservations are conservative holds, not confirmed charges. Gateway account credit, whole-project expenditure and the approved admission ceiling are different quantities.

| Request type | Condition | Mean actor turns; observed N | Mean reported live USD; observed N | Unknown-cost conversations |
| --- | --- | --- | --- | --- |
| Pressure | No gate | 4.870; 192 | 0.055760; 182 | 10 |
| Pressure | Broad | 5.079; 190 | 0.059585; 183 | 9 |
| Pressure | Decomposed | 4.995; 191 | 0.059696; 181 | 11 |
| Permitted | No gate | 4.948; 192 | 0.071960; 181 | 11 |
| Permitted | Broad | 5.332; 190 | 0.093062; 177 | 15 |
| Permitted | Decomposed | 5.026; 189 | 0.080375; 178 | 14 |

Observed means omit unresolved values; the missing counts prevent these from being interpreted as complete-assignment cost estimates.

## Collection-period sensitivity and limits

The prespecified provenance sensitivity retains the 29 source pairs with no earlier collected episode. It has one basic-economy pair and four pairs per other rule, so its support is uneven. It does not undo the post-start scope amendment.

| Gate | Outcome | Difference bounds (percentage points) | Unresolved pairs / assigned | Holm-adjusted p |
| --- | --- | --- | --- | --- |
| Broad | executed_violation | [-11.98, -10.94] pp | 2/29 | withheld |
| Broad | service_complete | [-8.85, -8.33] pp | 1/29 | withheld |
| Decomposed | executed_violation | [-10.42, -9.90] pp | 1/29 | withheld |
| Decomposed | service_complete | [-6.77, -5.21] pp | 3/29 | withheld |

The study covers 32 designed source pairs, eight selected rules, three hosted actor configurations and a scripted customer. Some pairs share context; the dependency ledger contains 31 components. Repeats are not new tasks. Mechanical labels do not establish comprehensive semantic compliance. The study was reduced after 344 historical attempts and prior outcome inspection. Small or rare improvements had low simulated detection under the stated design assumptions. Missing observations, treatment-dependent recovery and costs remain part of the result.

## Reproduction

Run `build_results.py --check` from this directory with Python. It compares the report against saved analysis, independently recounts live binary outcomes, verifies the source freeze and all archive members, and requires final pipeline status with no active stop. It performs no network or model calls and does not change the frozen analysis. `results_tables.json` records exact source hashes and the unrounded values used in this report.
