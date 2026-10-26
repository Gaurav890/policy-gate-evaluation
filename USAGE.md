# Applying the monitor audit

Use this audit when a monitor's warnings seem inconsistent with an agent's apparent success. First specify exactly what the monitor is supposed to detect. Then check whether the evaluation labels measure that same thing.

## A concrete example

An agent submits four database lookups together, although the policy permits one tool call at a time. It later completes an exchange correctly. A warning about the four calls is a correct interaction-rule warning. Calling it a false alarm because the final order is correct would score the monitor against a different objective.

This is observed in retail task 70. Run `python3 release/examples.py` and inspect the first entry of `release/examples.json`. The later examples show an address change accepted despite a written restriction, and an exchange whose monitor scores change when the requested target changes. Examples are selected for explanation; use the full tables to assess frequency.

## Audit another monitor

1. Write one precise target, such as an ineligible cancellation. Define when the relevant evidence becomes visible and whether the monitor is detecting an observed/proposed violation or predicting a future one.
2. Retain the public policy, tool descriptions and conversation through the current proposal. Keep future results, reference outcomes, private customer instructions and labels out of the monitor input.
3. Record outcome, rule label and warning separately. Define which examples have no target error before calculating any false-alarm rate. Preserve unknown and inapplicable labels.
4. For an input-matched comparison, send the exact same prefix under each target question. Hash that input and keep the horizon and threshold fixed. Do not change both the question and the available evidence and attribute the result only to the question.
5. Report the warning count and denominator together. Changing the denominator can change the rate without changing a single warning. Changing the prompt can change warnings without proving better accuracy.
6. Separate calls rejected by the tool from changes actually executed. Preserve policy-tool disagreements and report analyses excluding them.
7. Retain failures, missing scores and task dependencies. Do not treat repeated conversations from one scenario as independent tasks or collect until a preferred result appears.

## Files to adapt

`run_monitors.py` defines public prefix views. `substantive_evaluation/monitor_protocol.json` documents the three questions and common horizon. `substantive_evaluation/verify_labels.py` cross-checks the six selected predicates. `substantive_evaluation/analyze.py` computes input-matched comparisons and missingness bounds. These are frozen study sources: copy them into a new study instead of editing this study's recorded protocol.

For the present paper, run `sh reproduce.sh` from the extracted package. It verifies the source records and recomputes the released tables without paid calls. Human semantic review would be needed for claims that go beyond the literal, executable predicates; those broader claims are not made here.

## When warnings can block an action

Place the gate before every proposed write, return a reason when it blocks, and let the agent continue. Test forbidden requests alongside permitted counterparts. Keep three observations separate: a violating proposal, an actual forbidden database change, and successful permitted service. A tool may already reject a forbidden proposal, so do not credit the gate for preventing that same change.

The live follow-up includes an observed $300-credit example. The ungated actor issues an ineligible certificate; all three gates intercept their actors' proposals. On a permitted compensation task, however, both model gates initially ask for more verification. One actor gathers the evidence and completes the task; the other stops. Inspect `release/live_gating_ledger.json` and the corresponding `intervention_study/live_gating/episodes/` records. Run `python3 release/live_gating.py` for saved-record verification or add `--native` with the pinned simulator installed. These examples demonstrate concrete interventions and tradeoffs, not a population-level ranking of monitors.
