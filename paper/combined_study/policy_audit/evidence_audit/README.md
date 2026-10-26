# Policy evidence audit: findings and scope

**A programmatic evidence pass is complete for all 392 proposals and 576 nominally permitted conversations. Its checks cover selected observable requirements and retain unresolved policy interpretations.** This is an explicitly unblinded, post hoc audit. Rules were developed while inspecting saved examples; it is not a prospective validation study. No external model requests were made, and no missing output was filled.

## What the evidence establishes so far

The data do not support treating every extra block as unnecessary. Combining previously verified native predicates with conservative public-trace checks gives the following mutually exclusive accounting. Categories are assigned in table order, except monitor failure is always separate. A known violation is a reason to reject an action but does not imply that the gate adds protection beyond the tool's own checks.

| Evidence for a live blocked event | Broad | Decomposed |
| --- | ---: | ---: |
| Known violation of an original selected predicate | 39 | 35 |
| Additional supported action/prerequisite breach, including absent confirmation exchange or malformed passenger data | 7 | 3 |
| Current assistant message violates the recorded single-call/text separation rules; no preceding category applies | 10 | 0 |
| Full-policy status remains unresolved by these checks | 45 | 20 |
| Monitor unavailable; operational block | 1 | 1 |
| **All live blocks** | **102** | **59** |

Of the 74 known selected-rule violations above, 26 calls would already have been rejected by the native tool. Those blocks do not establish additional prevention of a state change. This accounting retains the frozen native replay distinction; it is not a new efficacy estimate.

There are **65 unresolved live block events**, plus two separately recorded monitor outages. Unresolved does not mean permitted or unnecessary. The audit does not establish an unnecessary-block rate. Current-message formatting is separated from the eligibility of the underlying database action; earlier message-format mistakes never justify a later otherwise-valid block in this accounting.

The same checks cover all 231 ungated shadow proposals, including allowed proposals and the missing decomposed decision. Broad monitoring blocked 36 known selected violations, 11 additional supported action/prerequisite breaches, four current-format-only cases, and 36 unresolved cases. Decomposed monitoring blocked 34, four, one, and 18 respectively, and retains one missing decision. The precise allowed/blocked/missing cross-tabs are in `summary.json`. Gate reasons are included only in the unblinded decision ledger, not used as a correctness oracle.

## Reference completion can include skipped procedures

| Condition | Frozen reference completions | Of these, writes executed without any post-request user reply |
| --- | ---: | ---: |
| No gate | 181 | 6 |
| Broad | 163 | 0 |
| Decomposed | 166 | 5 |

These eleven trajectories contain no user response after the initial request before the relevant database write, so the required disclosure-then-confirmation exchange is absent. The original completion counts remain unchanged. This gives a concrete example of why successful state completion need not mean compliant service; it does not establish that every other completion was compliant or rank the gates on a new endpoint.

Some other transcripts respond to an assistant's confirmation request by repeating facts and the original instruction. Those are **unresolved**, not automatically labeled violations for lacking the literal word “yes.” Likewise, a “yes” to the original request does not automatically authorize a different refund method. The exact meaning and scope of consent remain unresolved by these checks.

Recorded parallel tool calls or simultaneous assistant text and tool calls also occur in many completed trajectories: 113/181 ungated, 111/163 broad, and 102/166 decomposed reference completions contain at least one such structural departure. These are overlapping, conversation-level counts from saved message structure. They are not additional task failures, independent observations or proof that the database action itself was forbidden. Full semantic correctness, truthfulness and transfer behavior remain unassessed by this count.

## The 17 broad blocks previously clean on selected public predicates

Five show no post-request user reply before the write, establishing a missing confirmation exchange under the recorded policy. Three other confirmation-related cases contain later user wording that needs interpretation. Nine flight-change cases involve requirements outside the selected eligibility predicates, such as payment-profile membership or verifying the new itinerary. A requirement that a method be present in a profile does not itself name a mandatory tool call. These nine are not declared errors merely because the gate cites an absent profile read.

See the exhaustive 17-case list in `summary.json`, and the [case notes](case_notes.md) for directly inspected examples. The earlier eight confirmation-related gate rationales remain eight rationales; this audit deliberately does not convert all eight into authoritative labels.

## Coverage and limits

| Requirement | Implemented evidence check | Outside the implemented checks |
| --- | --- | --- |
| Explicit confirmation | Identifies writes with no later user reply; retains affirmative reply indices | Whether disclosure was sufficient and consent matched the exact action; nonliteral approval |
| Retail identity and ownership | Successful prescribed lookup and observed order owner | Full chronology of every information disclosure and multiple-user intent |
| Retail order status | Matching tool-observed pending/delivered status | Whether other available evidence satisfies the requirement when no tool state was observed |
| Refund destination | Original payment history or observed existing gift card | Authorization to substitute a method; ambiguous or incomplete evidence |
| Passenger changes | Observed count and documented date format | Preservation of other details, truthfulness of supplied fields and exact authorized change |
| Flight changes | Observed basic-economy constraint and profile payment eligibility | Routes, trip type, seats, pricing, cabin-change exceptions and disclosure |
| Compensation | Membership/insurance/cabin disjunction, matching cancellation-status observations and cancellation amount | Meaning of confirming facts, customer-only evidence, delayed-flight prerequisites and offer timing |
| Cancellation | Evidence gathered but no automatic permissive label | Reason, timing, flown segments and eligibility alternatives |
| Communication | Exact message-format structure | Unsupported claims, refusal appropriateness, transfer correctness and the full interaction |

Every proposal retains `whole_policy_permission: not_established`. Every conversation retains `whole_policy_compliance: not_established`. This conservatism is intentional: a partial checker must not manufacture comprehensive gold labels. The original eight predicates supply private-state evidence only for their stated scope. Clean selected predicates never establish full-policy permission.

## Evidence files and reproducibility

- `proposal_evidence.jsonl`: public-input hashes, exact clause lines, message indices, check status and explanations for all 392 proposals.
- `decision_evidence.jsonl`: all matched shadow decisions and live blocks, source paths, gate reasons and separate public/native evidence categories. No missing decision is treated as allow.
- `conversation_evidence.jsonl`: all 576 transcripts' write checks and format findings, joined to frozen completion records only for descriptive tabulation.
- `summary.json`: exact cross-tabs, input hashes, builder hash and limitations.
- `case_notes.md`: directly inspected examples and unresolved interpretations. These notes explain the recorded evidence and the limits of each interpretation.

Run `python paper/combined_study/policy_evidence_audit.py --check` to reproduce the evidence files without writing. Run `python paper/combined_study/verify_policy_evidence_audit.py` for adversarial boundary checks, including nonliteral consent, profile-versus-reservation lookup, compensation disjunctions and prior-versus-current message breaches. Both are offline. The input packet retains the exact policies, transcripts, proposal identifiers and source hashes.

## Reporting scope and next step

Use the completed evidence pass to explain why a blocked call, a prevented state change and a completed conversation measure different things. Report the 65 unresolved live blocks as unresolved; neither count them as unnecessary nor silently exclude them from the denominators. The audit does not certify full-policy permission or produce a comprehensive correctness rate.

The next work is manuscript integration: present the block accounting beside native replay, explain the eleven reference completions with skipped confirmation, and retain the finite-scenario scope, missing outcomes and post-start amendment. The four original formal tests remain withheld. No additional collection is part of this revision.
