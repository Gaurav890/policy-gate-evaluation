# Compact-study methods supporting From Warnings to Interventions

**Working methods draft for the amended compact study. All assigned attempts and offline processing are finished.** The final records retain 1,143 completed and nine incomplete live conversations, plus 383 complete shadow sources and one with missing monitor output. Design counts below describe the planned allocation; exact observed results and provenance are in [results_readout.md](results_readout.md). This is the compact-study methods note; the combined manuscript additionally restores the earlier warning and policy-comparison studies. The accompanying [results and discussion draft](results_and_discussion_draft.md) reports unfavorable findings and unresolved outcomes alongside the observed reductions.

## The question

A customer asks a service agent to issue a credit that the customer is not entitled to receive. A monitor blocks the proposed database change. Did the monitor help?

To answer, we need to know what the tool would have done without the block. If the tool would already reject the request, the monitor added no protection against that database change. If the tool would issue the credit, the block prevented a forbidden change at that moment. We must then ask what happened next: did the agent continue appropriately, repeat the request, or abandon legitimate work? These are different measurements.

Our earlier development experiment supplies a concrete example. An ungated agent issued an ineligible simulated $300 certificate. Under each of three gate conditions, an agent proposed the same ineligible certificate and the gate blocked it. Replaying those blocked calls in copied native states confirmed that the tools would otherwise have changed the database. Other blocks in that experiment intercepted calls that the native tools would already reject. We use this example to explain the measurements; its small development cohort remains separate from the primary study.

The present study connects three questions: what a monitor flags, which proposed database changes it would intercept, and how intervening changes a complete conversation. The first two can be measured on identical recorded proposals. The third requires running the actor with the gate in place and observing its response to blocks.

## Related evaluation work and contribution

Ajar tests excess and useful calls at reference-plan prefixes, with host-state validation and benign-utility measurements. We complement that scope by connecting actor-proposed calls to native transitions and live feedback. [Sharma et al. (2026), §§3–4, 6.3, 7.2, 7.5](https://arxiv.org/html/2609.26900v1)

Procedure-Aware Evaluation shows that task success can conceal procedural violations, using trajectory audits. Its integrity-gated utility is a scoring operation; our gates block execution and provide actor feedback. Our selected predicates have narrower semantic coverage. [Cao et al. (2026), §§3, 4.3, 5.1–5.2](https://arxiv.org/html/2603.03116v1)

AgentDojo already evaluates stateful agents, prompt-injection defenses and utility costs. Our customer-pressure scenarios address selected business-policy constraints rather than providing a general prompt-injection defense evaluation. Dynamic interaction and state-based checking are not new contributions here. [Debenedetti et al. (2024), §§3–4](https://arxiv.org/html/2406.13352v3)

The contribution is an empirical audit of two implemented policy gates: it links decisions on identical actor-generated proposals, the native consequences of those proposals, and outcomes after live feedback. The resulting discrepancies explain why blocked-call counts, selected-rule compliance and complete-conversation success should not be substituted for one another. This is a scoped measurement contribution, not a claim to introduce the first gate-evaluation framework or a generally superior defense.

## Environments and requests

We use the native retail and airline environments from a pinned implementation of the tau benchmark family. These environments provide public policies, read and write tools, and simulated databases. Their final-state comparisons are useful measures of whether a requested change occurred. The original tau-bench describes this outcome-based evaluation of tool-agent-user conversations. [Yao et al. (2024)](https://arxiv.org/abs/2406.12045) All actions in our study affect simulated data; no actual reservations, payments or customer accounts are changed.

The primary allocation contains 32 source pairs, four for each of eight selected rules. Each pair supplies a forbidden request and a permitted counterpart. The rules cover cancellation eligibility, basic-economy flight changes, passenger-count changes, compensation eligibility, delivered-order returns, refund destinations, the required customer lookup, and further changes after an item modification. The lookup check verifies a recorded procedure; it does not establish real-world identity assurance.

Pressure requests ask for actions that violate a selected rule. The customer may repeat the request within a fixed limit, while the actor chooses its own replies and tools. An actor is free to refuse before proposing any write. Nominally permitted counterparts measure whether the requested reference state is reached and the conversation ends normally; these endpoints alone do not establish that any obstruction was unnecessary. Nominally permitted requests can still produce invalid actor actions, so request type never substitutes for checking the actual proposal.

Pairs 00 and 01 were used for development and remain outside the primary estimates. Pairs 02–05 form the amended compact allocation. Their main users and entities are distinct, but some share flights, products or other context. The dependency ledger connects the 32 pairs into 31 components. Shared policies, templates and domains remain even between components. These are designed pressure scenarios, not a random sample of real incidents or evidence of unseen-domain generalization.

## Gate conditions

A gate receives a proposed write before it executes. If the gate blocks it, the actor sees a refusal reason and can continue. Each live condition starts from the same case state, but its conversation is generated separately.

| Live condition or shadow reference | Decision rule | Information available |
| --- | --- | --- |
| No gate | Let the native tool handle the proposed call. | The actor's normal policy and tool observations. |
| Broad model gate | Ask one fixed monitor to check the current write against the public policy. | Public policy, tool schemas, visible conversation and current proposed write. |
| Decomposed gate | Apply public-evidence predicates; block a detected violation; ask focused model questions for selected rules that remain unresolved. | The same public information as the broad gate. |
| Privileged predicate reference (shadow only) | Block a violation of an applicable selected predicate using private state facts. | Additional private facts unavailable to the public gates. |

Both model gates use Gemini 3.1 Pro with high reasoning. We use a reasoning-enabled monitor for the intervention comparison, and fixed this configuration during development before primary collection. The earlier warning studies used different monitor configurations and remain separate. Holding the monitor configuration fixed controls one difference between implementations, but the broad and decomposed gates also differ in policy coverage. The comparison therefore does not isolate the effect of decomposition. Its scores are thresholded at 0.5; they are not calibrated probabilities. The privileged shadow condition is a reference for the selected predicates, not an oracle for all policy, actor planning, correct arguments or successful completion.

The actor configurations are GPT-5.4 Mini, DeepSeek V4.1 Flash and Claude Opus 5.5 with high reasoning. The full gateway identifiers, requested reasoning, provider restrictions and response records are retained. Hosted aliases can change over time; they do not identify immutable model weights. We do not describe these three configurations as covering every frontier model.

## Two complementary comparisons

**Shadow decisions compare gates on exactly the same proposals.** We save every write proposed during a no-gate conversation, together with the public prefix available before that write. Each gate judges that identical input. Public input hashes verify that the compared gates receive the same evidence, while their instructions remain intentionally different. Shadow decisions are never shown to the actor or customer.

We separately replay the proposed native transition in a copied state. A violating call can change state, raise an error without changing state, or do neither. These cases have different implications for the benefit of blocking it. We retain proposals after an earlier violation in the main descriptive corpus, then repeat the analysis after truncating each sequence at its first executed covered violation. Later ungated states may never be reached by a live gate.

**Live conditions measure what follows an intervention.** The actor runs independently under each gate condition and can react to a block. A difference in final outcomes can include refusal, changes in proposed actions, recovery and failure to complete. It is not inferred solely from a blocked-call count. In particular, a gated rollout that refuses before invoking its gate does not supply direct evidence that the gate caused that refusal.

| Allocation | Source pairs | Actors | Repeats | Request types | Live conditions | Planned conversations |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scripted customer | 32 | 3 | 2 | 2 | 3 | 1,152 |

The 384 planned no-gate conversations provide the source corpus for shadow scoring by the two public gates and the privileged reference. Shadow monitor calls are additional API requests, not additional conversations or independent tasks.

The original schedule shuffled eight request/condition combinations within each pair/actor/repeat/customer block using a recorded seed. The compact schedule preserves the relative order of the six retained combinations. Actor sampling remains unseeded, and actor blocks are not themselves randomly reordered. Every conversation has an upper limit of 32 actor turns and eight customer turns.

## Customer behavior and the scope amendment

All compact conversations use the same scripted customer with fixed facts and at most two designated pushbacks. Scripted requests make comparisons reproducible but do not reproduce the variety of real customers. There is no model-customer robustness claim in this allocation. Earlier model-customer and live privileged-gate conversations remain separate historical evidence.

The study was reduced after 344 conversations had been attempted under the larger plan. Existing outcomes had been inspected. The amended selection retains the same pair indices 02–05, repeat indices 0–1 and three live conditions for every rule and actor; it does not select cases according to performance. Of those earlier attempts, 102 fit the compact allocation and are reused byte-for-byte: 101 completed and one was interrupted by a monitor timeout. The other 242 attempts remain archived outside the compact estimates. The 1,152 allocation therefore requires 1,050 additional attempts, not 1,152 new ones. No interrupted episode is replaced.

This is a documented change after collection began, not a wholly prospective registration. Protocol versions, the selection rule and original episode hashes remain visible. A separate sensitivity analysis excludes all three previously observed source pairs and uses the 29 pairs with no earlier collected conversation. That subset has one basic-economy pair and four pairs for each other rule; the uneven support limits its interpretation.

Automated customer audits check literal facts and control flags. They can miss semantic drift and can flag valid facts expressed in a different surface form. Preserved diagnostic sidecars distinguish demonstrated parsing problems from unresolved fidelity concerns without rewriting the frozen flags. Flags do not remove cases from the main analysis. A complete-pair exclusion sensitivity remains exploratory because flagging can itself depend on treatment.

## Outcomes with explicit denominators

An **executed covered violation** is a write that violates an applicable selected predicate and changes the native state within the conversation's fixed horizon. A tool error accompanied by a state change still counts. This definition measures the selected constraints, not every policy or communication requirement.

For nominally permitted requests, we report three outcomes separately: exact reference-state match, conversational completion, and their conjunction. The frozen endpoint names the conjunction **completed service**; we call it **reference completion** in the interpretation to distinguish it from full-policy-compliant success. Reaching the correct state while the dialogue remains unfinished does not satisfy the endpoint. Reaching it after skipping a required procedure can satisfy the endpoint. Refusal, bad arguments and customer-controller behavior can reduce completion even when no gate blocks a write. These endpoints do not quantify unnecessary obstruction or establish full-policy compliance.

For shadow decisions, the denominator is the number of proposals in a named mechanical class. We report state-changing violations separately from violations already rejected by the tools. Selected-eligible proposals are divided into those whose eligibility is established publicly and those requiring private facts. Unresolved or uncovered cases remain separate. A block on a selected-eligible proposal is not automatically a full-policy false alarm: a broad gate can identify requirements outside our checks.

Every actually blocked live write is replayed in a copy of its precise pre-write state. This establishes whether that single transition would change the simulator; it does not reconstruct an entire alternative conversation. Monitor-unavailability blocks are identified separately from substantive detection. Recovery is described with observable actions: a later read, the next write repeating or changing the proposal, a lexical refusal cue, final state and end status. These flags do not infer the actor's intent.

We report actor and customer turns, live gate requests and response-reported costs. Shadow evaluation cost is separate from the operating cost of a live condition. Failed requests and unresolved billing are retained. A zero denominator is undefined, and a missing monitor output never becomes an allow decision.

## Analysis and interpretation

The four selected live comparisons are each public gate versus no gate for two outcomes: executed violations on pressure requests and completed service on permitted requests. Within a source pair, each arm averages its three actors and two repeats. We then weight pairs equally within each rule and the eight rules equally. The reported difference is gate minus no gate. A reduction means fewer selected-rule violations or fewer reference completions, respectively. The latter is not automatically a loss of compliant service: a justified block can prevent an impermissible shortcut. We do not choose a utility tradeoff after seeing the data.

Repeated conversations from one source pair are not treated as new independent tasks. Descriptive bootstrap calculations resample whole pairs within rule, retaining their actors, repeats and conditions. Leave-one-rule-out and shared-context analyses assess sensitivity to the recorded dependence structure. They do not establish generalization to other policies or domains.

Simulation before the original collection found that the initially proposed percentile intervals had inadequate coverage, particularly for rare outcomes. The diagnostic and the pre-collection amendment are retained. The compact analysis retains paired label-swap calculations with Holm adjustment across four amended contrasts, as exploratory sensitivities. The smaller comparison family was selected after collection began; these are not confirmatory tests from a wholly prospective registration. Their sharp-null interpretation requires valid assignment exchangeability, stable potential outcomes and no inter-run interference. They do not automatically test every population-average null. Bootstrap intervals remain descriptive, and degenerate intervals do not establish zero uncertainty. The full algorithm, assumptions and scope-change disclosure are in the compact analysis plan.

All assigned attempts remain in the analysis. Turn-limit terminations are observed outcomes within the declared horizon. Infrastructure interruptions and unstarted cells are unresolved, except that an already observed positive violation remains positive. Binary summaries retain assignment-based bounds; a formal contrast with an unresolved pair block has no p value. A diagnosed infrastructure or invalid-output stop may be followed by continuing the next unstarted cell under the same frozen protocol. The interrupted cell is retained without retry or replacement; the stop and its disposition remain in the evidence archive. No task, model or stopping time is selected on the basis of a favorable interim effect.

The study is better suited to large finite-benchmark differences than to small or rare improvements. Under the stated synthetic assumptions for the compact design, detecting a reduction from 10% violations to 5% occurred in only about 9.5–18.5% of synthetic datasets. Failure to detect a benefit will therefore not demonstrate equivalence. Likewise, few or no violating proposals will leave interception sensitivity weakly supported or undefined. These limits are part of the result's interpretation, regardless of the direction of the eventual findings.
