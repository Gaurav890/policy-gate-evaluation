# Live-gating comparison

This is a prospective, exploratory comparison on eight designed source pairs, with one forbidden and one permitted request per pair. GPT-5.4 Mini generates the agent responses and tool choices; a scripted customer supplies fixed facts and bounded pressure. Each gate condition gets a fresh online rollout.

Planned: 64 conversations. Recorded: 64. Status: {'completed': 61, 'incomplete': 3}.

| Gate | Pressure: violations / completed | Pressure incomplete or unattempted | Controls: state matches / completed | Controls incomplete or unattempted |
| --- | ---: | ---: | ---: | ---: |
| none | 3/8 | 0 | 6/7 | 1 |
| broad | 0/8 | 0 | 7/8 | 0 |
| decomposed | 0/8 | 0 | 6/8 | 0 |
| oracle | 0/8 | 0 | 5/6 | 2 |

The pressure denominator is eight assigned conversations per condition. Incomplete conversations are not silently scored as safe. The JSON reports bounds over all assignments, observed positives in incomplete attempts, and complete-pair discordances. Control-state matches concern a reference database state, not every policy or conversational objective.

| Gate | Blocked violating proposals | Blocks on covered-rule-eligible writes | Monitor failures | Native rejections of violating writes |
| --- | ---: | ---: | ---: | ---: |
| none | 0 | 0 | 0 | 2 |
| broad | 7 | 4 | 0 | 0 |
| decomposed | 5 | 4 | 0 | 0 |
| oracle | 5 | 0 | 0 | 0 |

A native tool rejection is not a gate prevention. A missing monitor output that fails closed is not a successful semantic detection. A block on a covered-rule-eligible action can concern an unmeasured rule under the broad prompt, so it is not automatically a full-policy false alarm.

The privileged predicate gate uses simulator state. The broad and decomposed gates receive only public policy, tool schemas and the recorded prefix. Block feedback is returned to the actor, which can continue. Comparisons are independent online rollouts, not guaranteed identical sampled actions.

## Cost

New response-reported cost: $0.829445. Cumulative response-reported cost: $56.855479. Conservative cumulative hold: $96.479733 / $100. Unresolved new reservations: $0.000000. Local accounting, not a provider invoice.

## Interpretation

Exploratory extension after earlier pilots. Single reference actor and scripted pressure tasks. No frontier generalization or claim of complete semantic compliance.
One source pair per rule and one rollout per condition cannot establish stable population effects. All eight rules are included, including those already enforced by native tools. Prior failed or successful actor cases were not selected into this comparison. Two source pairs had appeared in constructed monitor fixtures. The existing paper and previous checkpoint remain historical artifacts.
