# Positioning against nearby evaluations

The combined manuscript restores the broader earlier literature and contains 55 cited references. PrefixGuard is updated to its 27 September 2026 v2, which connects learned-event warnings to finite-state diagnosis; Ajar v1 author order is corrected.

This is a focused comparison of primary papers, not an exhaustive systematic review or proof of novelty. The manuscript bibliography records the inspected versions; it includes Ajar v1, Procedure-Aware Evaluation v1 and AgentDojo v3. Numbers from different task sets, threat models and labeling procedures are not directly comparable.

| Approach | Measurement and overlap | Difference relevant to our claim |
| --- | --- | --- |
| [Ajar](https://arxiv.org/html/2609.26900v1), §§3–4, 6.3, 7.2, 7.5 | Tests required/permitted/excess calls at reference-plan prefixes; measures leakage and denial of useful calls. Includes host-state validation and benign-task utility. | Our shadow corpus contains calls actually proposed by actors; we link native transition effects to separate live gated trajectories. This complements generated privilege tests and does not supersede them. |
| [Procedure-Aware Evaluation](https://arxiv.org/html/2603.03116v1), §§3, 4.3, 5.1–5.2 | Audits trajectories across task utility, efficiency, interaction quality and procedural integrity. Demonstrates that outcome success can conceal violations. | Its integrity-gated utility rescales an evaluation score. Our gates intervene before execution and return feedback to the actor. Our selected predicates cover fewer semantic requirements. |
| [AgentDojo](https://arxiv.org/html/2406.13352v3), §§3.1, 3.4, 4.3 | Stateful agent evaluation with prompt-injection attacks, defenses, utility and security outcomes. | Our paired customer-pressure requests target selected business rules. Live interaction, state checks and utility costs are established evaluation ideas; this study examines their relationship to specific blocked writes. |

## Position supported by our evidence

Describe the paper as an empirical evaluation of two implemented policy gates, with a reproducible audit connecting identical proposals, native transitions and conversation outcomes. Its useful insight must come from the documented discrepancies between those measurements: native rejection can make an apparent interception redundant; selected eligibility can omit another valid policy requirement; and an allowed shadow call does not predict how an actor responds to live feedback.

Do not describe the generic safety–utility tradeoff, tool-call gating, dynamic evaluation, native replay, or checking procedure in addition to task completion as newly introduced here. Do not imply that Ajar lacks replay or state validation, or that Procedure-Aware Evaluation enforces runtime blocks. Do not rank our gates above those papers' systems using incomparable percentages.

The strongest remaining distinction is the evidence chain in these assigned customer-service cases, not a first-of-its-kind general framework. The rewritten manuscript integrates this comparison with the completed programmatic evidence pass, retaining its unresolved interpretations. Ten primary papers are cited; source metadata and versioned links are in `manuscript_references.json`. The evidence does not establish general superiority or a comprehensive policy-error rate.


## Additional primary sources used in the rewrite

| Source | Role in the manuscript |
| --- | --- |
| [Tau-bench](https://arxiv.org/abs/2406.12045v1) | Task-oriented tool interaction, reference-state evaluation and repeated-run reliability. |
| [Tau2-Bench](https://arxiv.org/abs/2506.07982v1) | Maintained benchmark context and the distinction from its dual-control telecom setting. |
| [ST-WebAgentBench](https://arxiv.org/abs/2410.06703) | Policy-constrained completion and violation-risk evaluation in web tasks. |
| [AgentHarm](https://arxiv.org/abs/2410.09024) | Harmful-request evaluation as a distinct threat model. |
| [ToolEmu](https://arxiv.org/abs/2309.15817v2) | Risk discovery with an emulated tool environment; contrasted with replay in the pinned native simulator. |
| [R-Judge](https://arxiv.org/abs/2401.10019) | Risk recognition from interaction records, distinct from runtime intervention outcomes. |
| [AgentSpec](https://arxiv.org/abs/2503.18666v3) | Existing customizable runtime enforcement; the present study does not claim to introduce that approach. |

Primary source metadata and the official TMLR author guide were checked on 24 October 2026. The paper is formatted as an anonymous working preprint, without a submitted or accepted status. The bibliography is deliberately focused on claims made in this rewrite rather than carrying over all references from the historical manuscript.
