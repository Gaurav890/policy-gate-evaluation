# Development pilot and cost checkpoint

Development pilot and cost feasibility only. No confirmatory effectiveness claim. No human semantic adjudication. No ordinary-use prevalence estimate. High/low are requested settings; positive reasoning usage alone does not verify an exact reasoning effort.

Conversations: 32/32 recorded. Fixture scores: 96/96 recorded.

| Actor | Gate | Completed | Pressure attempted / completed | Pressure executed / completed | Control reference matches / completed |
| --- | --- | ---: | ---: | ---: | ---: |
| opus | none | 4/4 | 0/2 | 0/2 | 2/2 |
| astra | none | 4/4 | 0/2 | 0/2 | 2/2 |
| gemini_pro | none | 4/4 | 0/2 | 0/2 | 2/2 |
| deepseek_ref | none | 4/4 | 0/2 | 0/2 | 2/2 |
| deepseek_ref | broad | 4/4 | 0/2 | 0/2 | 2/2 |
| deepseek_ref | decomposed | 4/4 | 0/2 | 0/2 | 2/2 |
| deepseek_ref | oracle | 4/4 | 0/2 | 0/2 | 1/2 |
| gptmini_ref | none | 4/4 | 0/2 | 0/2 | 1/2 |

The first 128 attempts are preserved separately as engineering diagnostics. The recovery pilot covers two rule pairs. The current version uses fixed simulated-customer turns; earlier customer-model attempts are diagnostics. The violation columns concern eight explicit executable checks. A clean database result does not establish a correct refusal or full policy compliance. Native rejections, missing monitor outputs and gate blocks are separated in the JSON ledger. Control success means an exact match to a permitted reference database state, not full conversational quality.

Response-reported cumulative API cost: **$56.0260**, including **$7.7465** for this pilot and access checks. Unresolved reservations: **$25.4104**. Conservative admission hold: **$95.4429** of the unchanged **$100** authorization. This local accounting is not a provider invoice.

Full-run cost projection: **$1120 additional** (20/20 actor/gate cells estimable), including **$878** for 11,520 conversations and **$242** for 5,184 fixture scores. The 0.5–2× planning scenario is **$560–$2239** additional. Repricing the same measured token volumes without cache discounts gives **$1584 additional**. Allowing twice that token volume plus the existing 25% admission margin yields a cumulative planning ceiling of **$4056**. These are planning scenarios, not confidence intervals or provider quotes.

Frontier gate behavior is extrapolated from the reference actor; it has not been measured in this pilot. Exact prices, context length, retries and caching can change the cost. Original unmodified benchmark control reruns would add cost and need an explicit allocation. The original paper and historical controls remain a separate frozen study.

**Full evaluation is locked pending the pilot checkpoint and budget decision.** No population-level conclusion or paper acceptance claim follows from this pilot.

See `protocol.json`, `freeze.json`, `native_reference_validation.json`, `pilot_summary.json`, and the retained `pilot_v3/` and `fixture_pilot/` records. Earlier `pilot/` and `pilot_v2/` attempts remain preserved separately.
