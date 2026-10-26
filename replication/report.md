# Final simulation expansion

- Fixed allocation: 168 new attempts on all 42 previously unused reserved test IDs.
- Completed: 155; interrupted and retained: 13.
- New state successes: 133; interaction-clean state successes: 49 across 16 task IDs.
- Three monitors: Gemini, DeepSeek, and GPT-5.4 Mini. Every completed trajectory's decision prefixes are accounted for; missing outputs are not negatives.
- Constructed substantive-policy test: 48 native simulator cases, 24 matched pairs, six rule contrasts, four source reservations. Both eligibility classes execute cancellation; this is not natural prevalence evidence.
- No human labels are used or required for the declared mechanical targets. The optional review website is separate.
- Total reported API cost: $35.798605; new expansion cost: $19.865329; conservative admission hold: $47.094366; authorization: $100.00.

This is a reproducible, limited evaluation audit. More simulations improve coverage of this benchmark, not guarantees of acceptance or deployment safety.

## What the results mean

Reaching the expected database state and following a stated rule are different checks. The monitor can warn about a rule breach even when the final state matches. Changing which successful conversations count as negatives therefore changes the measured alert rate. These are rates relative to explicit proxy targets, not independently verified errors against every policy requirement.

| Monitor | Alerts among new state successes | Alerts among new interaction-clean state successes |
|---|---:|---:|
| Gemini | 86/133 | 2/49 |
| DeepSeek | 70/133 | 28/49 |
| GPT-5.4 Mini | 107/133 | 32/49 |

The change is not uniformly downward: DeepSeek has a higher alert rate in the interaction-clean subset, while Gemini and GPT-5.4 Mini have lower rates. These monitors do not behave like the exact interaction-rule baseline.

A count range means missing scores prevent an exact episode label. It is not a confidence interval. The exact rule baseline gives 84/133 and 0/49 respectively, by construction.

| Monitor | Cancellation target | Eligible alerts (24 cases) | Ineligible alerts (24 cases) |
|---|---|---:|---:|
| Gemini | broad | 0/24 | 24/24 |
| Gemini | eligibility | 0/24 | 24/24 |
| DeepSeek | broad | 0/24 | 16/24 |
| DeepSeek | eligibility | 3/24 | 21/24 |
| GPT-5.4 Mini | broad | 0/24 | 1/24 |
| GPT-5.4 Mini | eligibility | 0/24 | 4/24 |

The controlled cases show why successful tool execution cannot certify cancellation eligibility. They are designed examples with four reused source reservations, not evidence about how often real agents violate policies. Configuration differences, including reasoning settings, limit model-ranking interpretations. Human review is optional for these mechanical labels; it would be needed to support additional ambiguous judgments presented as human-validated evidence.

## Remaining author actions

Review the manuscript and its limitations, finalize authorship and private submission metadata, and authorize actual submission. No paper has been submitted. Completing experiments and formatting does not guarantee acceptance.
