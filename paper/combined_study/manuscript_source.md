# From Warnings to Interventions: Evaluating Policy Enforcement in Tool-Using LLM Agents

## Abstract

Evaluations of policy gates for tool-using language-model agents often report warning rates, block rates or task success, but these measure different properties. We present an evaluation method that links each decision to its policy target, visible evidence, native execution consequence and subsequent task outcome. Across simulated retail and airline environments, the same saved warnings yield alert rates of 64.7% or 4.1% on successful conversations depending on whether the evaluation group also requires interaction-rule compliance. In 1,152 live conversations, two example gate designs block 161 writes: 48 would produce violations of the checked rules that would change the database, whereas 26 would already be rejected by the native tools. Relative to ungated runs, gating reduces observed executed violations by about ten percentage points and reference-task completion by six to nine points, accounting for unresolved outcomes. All ungated violations come from one of three actor configurations. Matched completion losses sometimes occur without a block, and some successful endpoints omit a required confirmation exchange. Linked records, native replay and executable checks let evaluators distinguish detection, added protection and task outcomes, while preserving missing observations and unresolved policy judgments.

## 1. Introduction

In our initial live study, an agent issues an ineligible $300 credit in an airline simulation. Under a gate, the agent proposes the same ineligible credit, but the call is blocked before execution and no certificate is issued. In the compact study, a gate blocks a refund to a disallowed destination that the native tool would reject anyway; the exact proposal and replay are indexed as `compact-refund-native-rejection` in `release/examples.json`. Both events increase the block count by one, but only the first adds protection against a database change. The credit example from our initial live study and the refund contrast expose a measurement problem: **what did the gate actually prevent, and what happened to the user's task afterward?**

Language-model agents carry out requests through tools [@yao2023react; @schick2023toolformer]. A monitor assesses proposed behavior; a gate uses that assessment to control execution. Warning rates describe decisions, replay describes immediate consequences, and task outcomes describe the continuing interaction. Substituting one for another can credit a gate for protection already supplied by the tool, count repeated blocks as multiple saved tasks, or treat a successful endpoint as evidence of a compliant procedure.

We organize the evaluation around three questions:

- **RQ1: What does a warning detect?** State the target and observation boundary, and compare decisions on identical inputs.
- **RQ2: What does a gate add?** Replay blocked calls in their saved preceding states to separate intercepted violations from native rejection.
- **RQ3: What happens to the task?** Follow the live conversation, measure reference completion, and check supported procedural obligations separately.

Our contributions are an evaluation method connecting these three questions, evidence that success, warning and block metrics diverge in practice, and linked records with executable checks. The compact intervention study is the primary evaluation: 32 designed scenario pairs, three actors, two repetitions and two example gate designs in the retail and airline environments of $\tau$-bench [@yao2024tau; @barres2025tau2]. Earlier studies establish why the warning target and observation boundary matter. We retain their separate designs rather than pooling them into a single sample.

Ajar evaluates defenses on generated reference-plan calls and also measures benign utility [@sharma2026ajar]; Procedure-Aware Evaluation rescores completed trajectories for procedural integrity [@cao2026procedure]. We evaluate gates on calls actors actually propose, replay each blocked call against native tools, and follow the live conversation afterward. This connects decision quality, immediate protection and subsequent behavior. Reproducible agent evaluation requires the evidence behind each link [@kapoor2025agents].

The compact results show about ten fewer executed violations per 100 pressure conversations and six to nine fewer reference completions per 100 nominally permitted conversations under gating. All ungated violations arise from one actor configuration. The contribution is a method for identifying what these measurements support, together with concrete disagreements between them; broader gate-effectiveness claims require a separate confirmatory study.

## 2. Framework and terminology

\label{sec:framework}

Figure \ref{fig:evaluation-flow} places the three questions along the decision chain. The public input is the policy, tool schemas, conversation prefix and current proposal. The monitor sees no future turns or private simulator state. A warning issued after a forbidden proposal becomes visible can still prevent execution, even when it is not an advance prediction.

{{EVALUATION_DIAGRAM}}

Let $s_t$ be the saved state before action $a_t$ and $T(s_t,a_t)$ its native execution. For each blocked call we record its selected-predicate status and whether $T$ changes the database, rejects the call or performs a no-op. Replay uses a private copy of $s_t$, leaving the live trajectory unchanged. The live actor receives feedback and can gather evidence, revise its proposal, repeat it or stop. Matching scenario, actor and repeat aligns initial assignments; it does not make independently sampled trajectories identical.

| Term | Operational definition | Does not identify |
| :--- | :--- | :--- |
| Public input | Policy, schemas, prefix and current proposal | Private facts or future turns |
| Warning | Monitor score crossing its fixed threshold | A prevented action |
| Boundary detection | Warning after the offending proposal is visible | Advance prediction |
| Covered violation | Breach of an applicable selected executable predicate | Every policy breach |
| Selected-predicate eligibility | No applicable selected predicate is violated | Full-policy permission |
| Reference completion | Normal dialogue termination and matching reference state | Procedural compliance |
| Interaction-clean | No measured interaction-rule violation ($V=0$), regardless of state success | State success or all-policy compliance |
| Clean success | State success and no measured interaction-rule violation ($G=1, V=0$) | All-policy compliance |
| Intercepted transition | Blocked covered violation that would change native state | A saved whole conversation |
| Enforcement overlap | Blocked violation the native tool would reject | Added state-change protection |
| Shadow decision | Gate score on a saved ungated proposal | A live continuation under that decision |
| Assignment bounds | Extremes compatible with missing binary outcomes | A confidence interval |
| Matched completion loss | Ungated completion paired with observed gated failure | Causation by a particular block |

Table: **Glossary and identification boundaries.** Definitions are used consistently across the research questions. \label{tab:glossary}

## 3. Studies at a glance

\label{sec:compact-design}

The compact allocation crosses 32 pairs (four per selected rule), three actor configurations, two repetitions, two request types and three live conditions, for 1,152 attempted conversations. Actors are GPT-5.4 Mini, DeepSeek V4.1 Flash and Claude Opus 5.5; both public gates use Gemini 3.1 Pro Preview. A scripted customer supplies fixed facts and at most two designated pushbacks. The eight rules concern cancellation, basic economy, passenger count, compensation, delivered returns, refund destinations, customer lookup and further changes after an item modification.

The **broad gate** checks the full public policy with one model judgment. The **decomposed gate** applies selected public-evidence predicates and focused model questions for unresolved facts. These are two example gate designs: policy coverage and decision structure both differ, so we do not rank architectures. The ungated condition retains native rejection. Shadow scoring compares both gates and a privileged selected-predicate reference on the same proposals from 384 ungated sources.

The records contain 1,143 normal terminations, eight infrastructure interruptions and one customer-turn-limit outcome. Shadow scoring is complete for 383 sources; one preserves a broad decision but lacks subsequent decomposed and privileged decisions. Four planned formal comparisons remain withheld under the frozen missingness rule. Appendix A details the post-start scope amendment, execution settings and source checks; Appendix B distinguishes descriptive bounds from the added exploratory analysis.

| Study | Source support | Completed / assigned conversations | Role | Answers |
| :--- | :--- | :--- | :--- | :--- |
| Original reserved-test cohort | 12 task IDs | 48 / 48 | Outcome/rule disagreement and warning timing | RQ1 |
| First test extension | 6 additional task IDs | 24 / 24 | Successes that follow the interaction rule | RQ1 |
| Remaining-test expansion | 42 additional task IDs | 155 / 168 | More task coverage and three monitors | RQ1 |
| Substantive-rule pilot | 12 training task IDs | 23 / 24 | Feasibility of selected policy checks | RQ1 |
| New-task policy study | 24 training task IDs | 96 / 96 | Matched monitoring questions on recorded inputs | RQ1 |
| Initial live-gating study | 8 designed pairs | 61 / 64 | Interception and subsequent behavior | RQ2–3 |
| Compact live-gating study | 32 designed pairs | 1,143 / 1,152 | Proposal, replay and conversation accounting | RQ1–3 |

Table: **Study roadmap.** Completion counts denote normal conversation completion, not task success or compliance. The 24 constructed cancellation pairs use four source reservations and are separate fixtures, not agent conversations. Compact shadow scoring reuses 384 ungated sources and adds no live conversations; 383 have complete output and one retains missing output. The compact sample includes 102 imported attempts from its larger parent plan, counted once. \label{tab:roadmap}



## 4. RQ1: What does a warning detect?

The earlier-study evidence in Sections 4.1–4.2 uses the monitors listed in Appendix E, including Gemini 3.8 Flash, rather than the compact gates based on Gemini 3.1 Pro Preview. Section 4.3 separately examines the compact gates.

### Changing the evaluation group versus changing the monitor

The earlier reserved-test cohorts contain 227 completed conversations across 60 task IDs. In the largest cohort, Gemini warns on 86/133 state-successful conversations (64.7%) but on only 2/49 successes that also satisfy the one-call interaction rule (4.1%). The warnings are unchanged; requiring interaction compliance changes the negative class. Figure \ref{fig:expanded-targets} contrasts these targets across monitors.

{{RQ1_TARGET_FIGURE}}

Changing the monitoring question can instead change actual decisions. Table \ref{tab:substantive-targets} reports the substantive new-task study’s matched comparison on 47 decision points. A separate, stricter conversation-level comparison contains nine conversations on four tasks. Within that strict subset, Gemini's broad-versus-focused alerts are two versus zero, while GPT-5.4 Mini's are four versus six. The narrower question thus moves warnings in opposite directions. That subset has no positive substantive violations, so it provides no sensitivity estimate.

{{RQ1_TARGET_TABLE}}

### Detection at the proposal boundary

Figure \ref{fig:timing} and Table \ref{tab:expanded-timing} align the first warning with the first visible violation. GPT-5.4 Mini alerts before the first measured violation in 21/48 original and 46/103 expansion conversations. Such alerts may concern another property; temporal precedence alone does not identify a forecast of the later violation. Alerts at the offending proposal show detection at a useful pre-execution boundary.

{{RQ1_TIMING_FIGURE}}

{{RQ1_TIMING_TABLE}}

### Identical proposals in the compact study

The ungated corpus supplies 231 writes: 21 would produce covered violating state changes, 15 violate a covered rule but are natively rejected, and 195 satisfy the applicable selected predicates. The gates receive identical public inputs for each write (Table \ref{tab:compact-shadow}). The privileged reference blocks all 36 selected violations and none of the selected-eligible proposals; one decision in the private-evidence class is missing.

{{TABLE_SHADOW}}

One decomposed miss concerns a basic-economy modification proposed without reading the reservation. Its focused check treats an economy argument and absence of visible basic-economy evidence as permission to allow. Private-state replay identifies a violating change; the broad gate blocks the same input because the reservation was not checked. This example separates unavailable evidence from evidence of permission.

The broad gate also blocks 17 publicly verified selected-eligible writes. Five lack any post-request confirmation reply, three retain ambiguous later confirmation wording, and nine invoke requirements outside the selected predicates. Those 17 blocks therefore cannot be labeled unnecessary from the mechanical negative class alone.

## 5. RQ2: What protection does a gate add?

### When the tool permits a policy violation

The cancellation fixtures hold the proposed operation fixed while changing eligibility facts. All 48 fixtures execute, including 24 ineligible cases, demonstrating a substantive rule not enforced by the native tool. Gemini detects all 24 ineligible cases under both questions; GPT-5.4 Mini detects only one under the broad question and four under the eligibility question (Table \ref{tab:policy-lab}). A narrow question does not uniformly repair monitor capability.

{{RQ2_CANCELLATION_TABLE}}

### Native replay of live blocks

Broad gating blocks 102 writes and decomposed gating blocks 59. Replay partitions these 161 events by their immediate native consequence (Table \ref{tab:compact-blocks}). Across both gates, 48 blocks intercept violating state changes, while 26 duplicate native rejection. The latter can be valid enforcement decisions without adding protection against that transition.

{{TABLE_BLOCKS}}

The remaining events require distinct interpretation: selected-eligible calls can violate other policy obligations, and two blocks result from unavailable monitors. Repeated interceptions also need not protect distinct tasks. After a broad block, the actor's next write repeats the same proposal in 44/102 events, changes it in one and is absent in 57. Under decomposed gating the corresponding counts are ten, one and 48. Revised writes are rare in these records; the counts favor evaluating recovery explicitly rather than treating a blocking reason as sufficient evidence of repair.

## 6. RQ3: What happens to the task?

### Executed violations and reference completion

Each condition contains 192 pressure and 192 nominally permitted assignments. Table \ref{tab:compact-live} retains unresolved outcomes in those denominators; Figure \ref{fig:bounds} plots gate-minus-ungated differences on one scale. The violation differences range from -10.42 to -9.38 percentage points for broad gating and -9.90 to -9.38 for decomposed gating. Completion differences range from -9.38 to -8.33 and -7.81 to -6.25 points. Missing-value assignments cannot reverse either direction in these runs.

{{TABLE_LIVE}}

{{FIGURE_OUTCOMES}}

Normal permitted-dialogue terminations are 192, 190 and 188; reference completions are 181, 163 and 166. The decomposed condition has 189 observed turn counts because the customer-turn-limit record contributes a turn count but not a normal termination. Appendix B reports operating burden separately: response-reported compact cost totals $83.04, with 88 unknown-cost requests and $3.46 in unresolved reservations.

### Concentration by actor and matched exploratory contrasts

GPT-5.4 Mini accounts for all 21 ungated executed violations. Its violation counts are 21/64, 1/64 and 2/64; its permitted completion counts are 53/64, 38/64 and 42/64. DeepSeek and Opus each have zero ungated violations in 64 pressure assignments. Actor-specific paired bounds appear in Table \ref{tab:paired-actors}; the artifact also reports each rule, scenario and scenario-by-actor cell.

{{TABLE_PAIRED_ACTORS}}

All Mini outcomes are observed. We add unplanned exact McNemar tests and sensitivities that keep repeated runs together within scenarios and shared-context groups (Appendix B). The four nominal exact values range from $1.9\times10^{-6}$ to 0.0347; the context-group sensitivities after four-comparison Holm adjustment range from 0.0020 to 0.0415. These exploratory calculations do not restore the withheld original comparisons or remove post hoc actor selection.

### Do completion losses contain blocks?

Matching nominally permitted runs identifies 16 observed completion losses under broad gating; eleven contain a block and five do not. Decomposed gating has 18 losses, nine containing a block, alongside six completion gains. Two broad and three decomposed outcomes remain unresolved (Table \ref{tab:completion-losses}). Fifteen broad losses and seventeen decomposed losses involve Mini.

{{TABLE_LOSSES}}

This accounting connects intervention records to lost completions without assuming every loss follows a block. It also shows that gains offset some decomposed losses. A block's presence is an association on separately sampled trajectories: it does not establish that removing the block would recover the task. Of the 20 blocks in observed losses, 15 remain unresolved under the programmatic policy audit. These unresolved judgments prevent estimating how many of those blocks were unnecessary.

### Endpoint success and policy evidence

The programmatic audit covers 392 distinct proposal inputs and all 576 nominally permitted conversations. It identifies 74 live blocks with selected-predicate violations, ten with additional supported action/prerequisite breaches, ten with only a current-message format breach, 65 unresolved cases and two unavailable-monitor events (Table \ref{tab:compact-audit}).

{{TABLE_AUDIT}}

Among reference completions, six ungated and five decomposed trajectories execute a write without any user reply after the initial request. The required disclosure-then-confirmation exchange is absent. Conversely, a later reply need not contain the literal word “yes” to express approval; ambiguous scope of consent remains unresolved. Endpoint success and supported procedural compliance therefore require separate checks.

The programmatic checks establish specific supported objections, not a comprehensive unnecessary-block rate. The 65 unresolved blocks remain a limitation; they cannot be counted as either justified enforcement or unnecessary obstruction. Appendix C distinguishes these interpretations without assigning unsupported labels.

## 7. Discussion and practitioner guidance

\label{sec:use}

For this allocation, broad gating corresponds to about ten fewer executed violations per 100 pressure conversations and eight to nine fewer reference completions per 100 nominally permitted conversations. The violation reduction and most completion losses occur in one actor configuration. Eleven of the sixteen observed broad completion losses contain a block; five do not. These separate denominators describe a protection–utility tradeoff in the measured allocation, not a net-benefit score over a deployment distribution.

Following the emphasis on measurement and documented risk context in the NIST frameworks [@nist2023rmf; @nist2024genai], evaluation should retain a linked record for each decision: the declared target, visible input, proposed action, native replay class, block feedback and eventual task outcome. Report blocks that overlap native rejection separately from intercepted state changes. Report repeated proposals and recovery alongside block totals. Use a full-policy permission assessment before interpreting selected-eligible blocks as obstruction. This makes disagreement between metrics inspectable instead of resolving it by choosing one preferred metric.

The observed repetition after blocks suggests a practical design question: does feedback identify the missing evidence or a permitted next step that the actor can use? A future evaluation should compare recovery behavior under controlled feedback while matching policy coverage. The present two gate designs do not isolate that mechanism. More repetitions of the same scenarios would also leave breadth unresolved; a confirmatory study should freeze fresh cases, meaningful violation opportunities across actors and missingness handling before collection.

The contribution is an evaluation procedure, not a new runtime constraint language. It complements static permission tests by examining realized proposals and continuation, and complements endpoint rescoring by identifying which transitions an intervention actually prevents. Practitioners can apply the accounting even when the policy engine is deterministic, provided they preserve the same evidence boundaries.

## 8. Limitations

**Internal validity.** The compact scope was amended after 344 parent-plan attempts existed; 102 matching records were imported and 1,050 new ones collected. Prior outcomes had been inspected. Order was only partially randomized and hosted sampling was unseeded. Different gate conditions generate different trajectories. Replay assumes the pinned simulator is correct and covers only one transition. The completion-loss association is not causal mediation, and the post hoc audit was developed unblinded.

**Construct validity.** Selected predicates cover eight requirements, not complete policy permission. Early interaction-rule violations can concern harmless reads; their rates cannot be generalized to harmful writes. Sixty-five live blocks remain semantically unresolved, preventing a comprehensive unnecessary-block estimate. A nominally permitted request can still be implemented incorrectly. Endpoint checks omit some procedural obligations, and monitor scores do not establish probability calibration. The two gates differ in both coverage and structure.

**External validity.** The compact study uses 32 designed pairs in two simulated domains, a scripted customer and one monitor configuration. All ungated violations occur in one actor. Pairs share policies, templates and contextual entities; hosted aliases can drift. The earlier 60 task IDs contain 51 exact reference-operation sequences, and cancellation fixtures reuse four reservations. Extensions were designed after earlier findings. The strict new-task subset has no positive violations. External CPU-baseline reproduction supplies no transfer estimate on these conversations.

**Statistical conclusion validity.** The compact allocation retains nine incomplete live records and one shadow source with missing output. Earlier studies also retain interrupted conversations and missing monitor scores. Four planned formal comparisons remain withheld. Assignment bounds address missing-value ambiguity, not scenario-population uncertainty. Exact actor-specific tests are unplanned, assume exchangeability at the reported unit and do not correct actor selection; shared contexts limit effective replication. Earlier bootstrap diagnostics and descriptive intervals are preserved, not substituted for confirmatory evidence. Cost means omit missing billing.

## 9. Related work

**Task and procedural evaluation.** $\tau$-bench evaluates tool-agent-user interactions through final database comparisons and repeated-trial reliability [@yao2024tau]; $\tau^2$-bench extends evaluation to dual control [@barres2025tau2]. We use its retail and airline tools, not the dual-control telecom setting. Procedure-Aware Evaluation separates utility, efficiency, interaction quality and procedural integrity [@cao2026procedure], while ST-WebAgentBench evaluates task completion under policy [@levy2024stweb]. Our gates intervene before execution and return feedback; our executable policy checks have narrower semantic coverage.

**Permission and enforcement.** Ajar constructs required, permitted and excess calls at reference-plan points, using benchmark information and state validation where applicable, and measures denial, excessive privilege and benign utility [@sharma2026ajar]. Our inputs are actual actor proposals linked to native consequences and separate live continuations; unproposed excess calls remain outside coverage. AgentSpec supplies a runtime-constraint language [@wang2025agentspec]. We evaluate two fixed gate designs rather than introducing a new language.

**Risk and adversarial evaluation.** AgentDojo and InjecAgent study prompt injection [@debenedetti2024agentdojo; @zhan2024injecagent]; AgentHarm and Agent-SafetyBench cover malicious requests and broader safety failures [@andriushchenko2024agentharm; @zhang2024agentsafety]. Our requests target business-policy violations. ToolEmu investigates risks through model-emulated execution [@ruan2024toolemu], whereas we replay pinned native tools. R-Judge evaluates recognition of recorded risk [@yuan2024rjudge], a distinct question from an intervention's continuation effect.

{{EARLIER_RELATED_WORK}}

## 10. Conclusion

Evaluating a policy gate requires connecting what it detects, what it prevents and what happens afterward. In these studies, changing the evaluation target changes the interpretation of saved warnings; 48 blocked writes intercept covered violating transitions while 26 duplicate native rejection; and lower executed violations coexist with lower reference completion. Some completion losses contain no block, and some successful endpoints omit required confirmation. Linked proposal records, native replay and continuation accounting make those differences explicit. The resulting evidence supports precise intervention claims within the observed allocation, while leaving broader effectiveness and unresolved permission judgments for further study.

## Reproducibility {.unnumbered}

The public artifact is available at [github.com/Gaurav890/policy-gate-evaluation](https://github.com/Gaurav890/policy-gate-evaluation), release `v1.1.1`; its [complete tagged source ZIP](https://github.com/Gaurav890/policy-gate-evaluation/archive/refs/tags/v1.1.1.zip) is the downloadable supplementary package, including the paper, saved evidence and reproduction scripts. It provides linked records, study-specific provenance and offline scripts. From an isolated environment, `python paper/combined_study/reproduce_principal.py` checks the compact evidence and regenerates the principal tables, actor/rule/scenario exports, exploratory tests and manuscript sources without model calls. Appendix D gives the artifact map. Original receipt commitments and sanitized released-byte hashes are kept distinct; missing outputs are not filled. The release README records the environment and checks actually completed.

## Broader impact {.unnumbered}

All bookings, refunds, identities and account changes in the experiments are simulated. The evaluation method can help distinguish additional protection from redundant blocking and reveal lost task utility. A foreseeable misuse is presenting narrow predicate checks or favorable aggregate counts as certification of deployment safety. We therefore retain coverage, missingness and provenance information alongside every reported result and do not recommend automatic deployment from these measurements alone.

{{REFERENCES}}

{{APPENDIX}}

## A. Execution and design details


The benchmark revision recorded in the project is `b7ea9074c1cba482b30687fecdb5c8425fd6f619`. Policies, native tools, scenario construction, and the relevant study sources are covered by the frozen artifact checks. Main pair indices 02-05 are distinct from development indices 00-01. Each selected rule has four pairs, and each pair has six actor/repeat cells per request type and live condition.

| Role | Requested gateway identifier | Provider route | Reasoning |
| :--- | :--- | :--- | :--- |
| Actor | `openai/gpt-5.4-mini` | openai | none |
| Actor | `deepseek/deepseek-v4.1-flash` | baseten | none |
| Actor | `anthropic/claude-opus-5.5` | anthropic | high |
| Both public gates | `google/gemini-3.1-pro-preview` | google | high |

Table: **Requested configurations.** Identifiers are historical collection settings. The protocol also retains a customer-model field inherited from the larger plan; compact collection used the scripted controller and made zero customer-model requests. \label{tab:compact-configurations}

The output cap is 8,192 tokens, the model-score threshold is 0.5, and the schedule seed is 20261012. The original within-block shuffle contained eight request/condition combinations; the compact schedule retains the relative order of the six selected combinations. The seed controls schedule construction, not hosted model sampling. Actor and customer limits are 32 and eight turns. The scripted controller uses fixed facts, refusal precedence, completion variants, and at most two marked pushbacks.

The eight retained infrastructure interruptions comprise six GatewayError and two RuntimeError terminations. The single administrative customer-turn-limit record remains an observed outcome. All 1,143 normally completed records use the customer-stop termination. The shadow source with missing output is an airline-compensation permitted case for the DeepSeek actor; its broad decision is retained while its decomposed and subsequent privileged-reference decisions remain missing.

Before the compact amendment, 344 attempts existed under the larger schedule. The compact set imports 102 matching records and excludes 242 nonmatching attempts; it then adds 1,050 new attempts. This accounting preserves the allocation's total of 1,152 without counting the imported records twice. A 121-file source freeze and 6,625 archived request receipts are checked by the reporting pipeline. These checks establish byte consistency and provenance, not a broader claim of behavioral correctness.

### Compact scenario construction and analysis



The compact study uses the native airline and retail tools from a pinned revision of the maintained  $\tau$ benchmark implementation [@yao2024tau; @barres2025tau2]. All writes affect simulated records. Each source pair contains a pressure request targeting a selected violation and a nominally permitted counterpart. We use four pairs for each of eight rules: cancellation eligibility, basic-economy modification, passenger-count changes, compensation eligibility, delivered-order returns, refund destinations, the prescribed customer lookup, and further modification after an item change. The lookup predicate checks an observable procedure, not real-world identity assurance.

The allocation is

$$32\ \text{pairs}\times 3\ \text{actors}\times 2\ \text{repeats}\times 2\ \text{request types}\times 3\ \text{conditions}=1{,}152.$$

The actor configurations are GPT-5.4 Mini, DeepSeek V4.1 Flash, and Claude Opus 5.5. The last requests high reasoning; the first two request none. Both public gates use Gemini 3.1 Pro Preview with high reasoning. These are hosted aliases, not immutable weight snapshots. Table \ref{tab:compact-configurations} lists the requested identifiers and routes; the execution limits are given immediately below that table.

All compact conversations use the same scripted customer, with fixed facts and at most two designated pushbacks. Conversations are bounded by 32 actor turns and eight customer turns. The actor chooses its own actions and may refuse before proposing a write. Consequently, a pressure assignment does not guarantee an opportunity for the gate to intervene. Similarly, a nominally permitted request does not guarantee that the actor's proposed implementation is valid.

The 32 pairs have distinct main entities and users but retain shared policies, templates, and some contextual entities. A recorded dependency ledger links them into 31 shared-context components. Repeated executions are not new tasks, and these designed cases are not a random sample of deployment incidents.

### 3.2. Live gate conditions

The **ungated condition** sends actor proposals to the native tools. Tool-level rejection remains active. The **broad gate** asks one fixed monitor to assess the current write using the full public policy, tool schemas, visible conversation prefix, and proposed arguments. The **decomposed gate** applies selected public-evidence predicates, blocks a detected violation, and asks focused model questions when applicable selected requirements remain unresolved. Model scores are thresholded at 0.5; they are decision scores rather than calibrated probabilities.

Public gates do not receive private simulator facts or reference outcomes. When a gate blocks a write, the actor receives feedback and may continue. An unavailable monitor produces a separately identified fail-closed event. Each live condition starts from the same case state, but generates its own conversation. The broad and decomposed implementations differ in policy coverage as well as decision structure, so their comparison does not isolate decomposition alone.

### 3.3. Identical-proposal decisions and native replay

The 384 assigned ungated conversations supply the shadow corpus. Every proposed write is paired with the exact public prefix available before execution. Both public gates score that identical input; hashes verify equality of the evidence presented. Shadow decisions are not returned to the actor or customer. A privileged predicate reference additionally uses private facts for the selected rules. It is evaluated only in shadow and does not certify full-policy compliance.

Native replay executes each proposal in a copy of the appropriate simulator state. This separates a violating call that changes the database from one already rejected by the tool. Every blocked live write is similarly replayed from its precise pre-write state. A replay establishes the consequence of a single proposed transition, not the outcome of an entire counterfactual conversation. In particular, live blocks change the proposal sequence, making the broad and decomposed live block corpora treatment-dependent.

The main shadow summary retains all observed ungated proposals. A sensitivity truncates each sequence at its first executed covered violation, because later ungated states may not be reached under intervention. The truncation leaves the observed class counts unchanged in this corpus.

### 3.4. Scope amendment and provenance

The compact allocation was selected after 344 attempts under a larger plan, with earlier outcomes already inspected. The selection retained pair indices 02-05 and repeats 0-1 uniformly across the eight rules and three actors, and retained the ungated, broad, and decomposed live conditions. It did not select cells according to their performance. Nevertheless, this post-start change means the full study is not a wholly prospective registration.

Of the earlier attempts, 102 fit the compact allocation and were reused byte-for-byte: 101 completed and one was interrupted. The remaining 242 attempts stay outside these estimates. Compact collection added 1,050 attempts. Interrupted episodes were not replaced. The schedule retained the relative order of selected cells from the original shuffled within-block allocation; actor sampling was unseeded and actor blocks were not globally randomized.

A provenance sensitivity retains the 29 source pairs with no earlier collected conversation. It has one basic-economy pair and four pairs for each other rule, so the support is uneven. Earlier development and warning-monitor studies motivate the question but are not pooled into the compact sample. Appendix D maps the results to saved artifacts.

### 4.1. Three distinct measurement levels

At the **proposal level**, a gate returns allow, block, or missing. We group ungated proposals by selected-predicate eligibility and native consequence, retaining the distinction between facts established publicly and facts available only privately. Selected eligibility does not mean that the full policy permits the action.

At the **transition level**, an executed covered violation requires both a violation of an applicable selected predicate and a native state change. A tool error accompanied by a state change still counts. A violating call that the native tool rejects without changing state is recorded separately. For a live block, native replay measures the transition that was intercepted; it does not demonstrate a net improvement over the remaining conversation.

At the **conversation level**, the pressure outcome is whether at least one executed covered violation occurs within the fixed horizon. On nominally permitted requests, **reference completion** requires both normal dialogue completion and an exact reference-state match. The frozen endpoint calls this completed service. We use the narrower name because the endpoint can be satisfied despite an omitted procedure. State matching and dialogue termination are also reported separately.

### 4.2. Missing observations and paired summaries

All assigned cells remain in the denominators. Infrastructure interruptions leave unobserved binary outcomes unresolved; an already observed positive violation remains positive. A turn-limit termination is an observed fixed-horizon outcome. A missing shadow output is neither a block nor an allow.

For an outcome with $k$ observed positives, $m$ unresolved values, and $n$ assigned runs, the assignment bounds are $[L,U]=[k/n,(k+m)/n]$.

These bounds describe uncertainty from missing values in the assigned runs. They are not confidence intervals. Contrasts average the three actors and two repeats within each pair, then weight pairs equally within rule and the eight rules equally. Gate-minus-no-gate bounds use the corresponding worst-case unresolved assignments. The balanced main allocation makes its aggregate differences consistent with these weights; the provenance sensitivity retains equal rule weighting despite uneven pair counts.

The four planned comparisons are each public gate versus no gate for pressure violations and nominally permitted reference completion. The frozen missingness rule withholds a formal comparison when any source-pair block is unresolved. All four comparisons meet that condition, so the original analysis reports neither p values nor formal inferential intervals. Preserved pair-bootstrap calculations are descriptive; earlier calibration had found inadequate coverage for the originally proposed percentile intervals. The separate actor-specific analysis below is explicitly unplanned and does not replace these comparisons.

### 4.3. Programmatic policy-evidence audit

After collection, we applied conservative checks to all 392 distinct proposal inputs (231 ungated writes and 161 live blocks) and all 576 nominally permitted conversations. The audit is unblinded and post hoc: the rules were developed while inspecting saved examples. It records policy clauses, message indices, source hashes, and uncertainty, without making new model calls or changing the frozen endpoints.

The checks cover observable prerequisites and action constraints, including the absence of any post-request confirmation reply, observed order state, refund destinations, passenger-count and date-format evidence, and selected flight and compensation facts. Message-format departures are kept separate from the eligibility of the database action. The audit does not infer non-consent merely because a reply lacks the literal word "yes," invent a requirement to call one named tool, or use an earlier formatting mistake to justify a later block. Unsupported interpretations remain unresolved. Appendix C specifies the coverage and accounting order.


## B. Supplementary outcome accounting

| Actor | Outcome | No gate | Broad | Decomposed |
| :--- | :--- | ---: | ---: | ---: |
| GPT-5.4 Mini | Pressure violations | 21/64; 0 | 1/64; 0 | 2/64; 0 |
| DeepSeek V4.1 Flash | Pressure violations | 0/64; 0 | 0/64; 1 | 0/64; 0 |
| Claude Opus 5.5 | Pressure violations | 0/64; 0 | 0/64; 1 | 0/64; 1 |
| GPT-5.4 Mini | Reference completion | 53/64; 0 | 38/64; 0 | 42/64; 0 |
| DeepSeek V4.1 Flash | Reference completion | 64/64; 0 | 63/64; 1 | 61/64; 2 |
| Claude Opus 5.5 | Reference completion | 64/64; 0 | 62/64; 1 | 63/64; 1 |

Table: **Actor-specific counts.** Cells show observed positives / assigned, followed by unresolved outcomes. Reference-completion rows concern nominally permitted requests.

| Request | Condition | Mean turns; observed n | Mean live USD; observed n | Unknown-cost runs |
| :--- | :--- | ---: | ---: | ---: |
| Pressure | No gate | 4.870; 192 | 0.056; 182 | 10 |
| Pressure | Broad | 5.079; 190 | 0.060; 183 | 9 |
| Pressure | Decomposed | 4.995; 191 | 0.060; 181 | 11 |
| Permitted | No gate | 4.948; 192 | 0.072; 181 | 11 |
| Permitted | Broad | 5.332; 190 | 0.093; 177 | 15 |
| Permitted | Decomposed | 5.026; 189 | 0.080; 178 | 14 |

Table: **Observed operating burden.** Missing costs are excluded from the means and retained in the last column. Turn and cost summaries have different observed denominators. The 189 decomposed permitted turn counts include the customer-turn-limit record, in addition to 188 normal terminations. Dollar means use three decimal places; the machine-readable tables preserve full precision.

| Gate | Outcome | Main bounds (pp) | Main unresolved pairs | 29-pair sensitivity (pp) |
| :--- | :--- | ---: | ---: | ---: |
| Broad | Executed violation | -10.42 to -9.38 | 2/32 | -11.98 to -10.94 |
| Broad | Reference completion | -9.38 to -8.33 | 2/32 | -8.85 to -8.33 |
| Decomposed | Executed violation | -9.90 to -9.38 | 1/32 | -10.42 to -9.90 |
| Decomposed | Reference completion | -7.81 to -6.25 | 3/32 | -6.77 to -5.21 |

Table: **Gate-minus-ungated difference bounds.** All four planned formal p values remain withheld. The sensitivity has 2, 1, 1, and 3 unresolved pairs in row order, and unequal pair support across rules. Bounds are not inferential intervals.

The archive also retains pooled-proposal and supported-pair shadow summaries, first-violation truncation, actor and rule breakdowns, and descriptive source-pair bootstrap calculations. The four selected formal comparisons would have used paired label swaps and Holm adjustment, subject to the declared assumptions and missingness rule. Because those rules withhold every comparison here, the paper makes no confirmatory claim based on these calculations. The earlier simulation diagnostics are retained rather than used to select a favorable analysis after collection.

### Paired differences by rule

{{TABLE_PAIRED_RULES}}

Scenario and scenario-by-actor rows are distributed in `paired_effects.csv`. The export retains all assigned blocks, including zero-event and incomplete cells. Its ranges address missing binary values only. With four designed pairs per rule, they are not estimates of uncertainty over a population of scenarios.

### Exploratory actor-specific paired tests

All 64 matched outcomes per condition are observed for GPT-5.4 Mini. We selected this actor after inspecting the concentration of violations, and added these analyses after collection. For discordant counts $b$ (ungated positive, gated negative) and $c$ (ungated negative, gated positive), the nominal two-sided exact McNemar value is $\min\{1,2\Pr[\mathrm{Binomial}(b+c,1/2)\leq\min(b,c)]\}$. Repeated runs within a scenario may be dependent, so the run-level test is not sufficient for inference.

We also enumerate exact sign flips of paired differences, keeping both repetitions together within each of 32 scenarios, and then within the 31 recorded shared-context components. Table \ref{tab:exploratory-tests} gives the nominal test and the context sensitivity, with Holm adjustment across the four actor-specific comparisons. The CSV retains both cluster definitions and all raw and adjusted values. Cluster exchangeability remains an assumption; adjustment does not correct post hoc selection of the actor or analysis. These results are exploratory evidence within this allocation, not restored preregistered tests or an estimate of a population effect.

{{TABLE_EXPLORATORY}}

### Completion-loss accounting

An observed loss requires an ungated reference completion and an observed gated non-completion for the same scenario, actor and repeat. A gain reverses those values. Unknown gated outcomes remain a separate category. Broad gating has 163 both-complete pairs, 11 both-fail pairs, 16 losses, zero gains and two unknowns. Decomposed gating has 160 both-complete pairs, five both-fail pairs, 18 losses, six gains and three unknowns. Thus the aggregate completion shortfalls are $16-0+2=18$ and $18-6+3=15$ when counting observed positives; the unknown terms are not established losses.

Each loss containing a block has exactly one blocked write. Of the eleven broad blocks in losses, two violate a selected predicate, one has only a current-message format finding and eight remain unresolved. Of the nine decomposed blocks in losses, one violates a selected predicate, one has an additional supported action/prerequisite breach and seven remain unresolved. No independent annotation labels have been collected, so the number judged unnecessary is unknown. The case export retains episode identifiers, block indices and evidence categories for inspection.

## C. Programmatic evidence checks and interpretation boundaries

| Requirement | Evidence used | Boundary retained |
| :--- | :--- | :--- |
| Confirmation | Any user reply after the initial request, disclosure context, and write boundary | Nonliteral approval and the precise scope of consent may remain unresolved. |
| Retail lookup and ownership | Successful prescribed lookup and observed order owner | Does not establish full correctness of every prior disclosure or request. |
| Order state | Matching observed pending/delivered state | Missing tool evidence is not automatically a violation. |
| Refund destination | Original payment history or an observed existing gift card | Permission to substitute a method requires separate contextual evidence. |
| Passenger modification | Observed passenger count and documented date format | Preserving other details and matching the requested change remain distinct. |
| Flight modification | Observed basic-economy status and payment-profile facts | Routes, seats, price, exceptions, and disclosure are not comprehensively checked. |
| Compensation | Membership/insurance/cabin alternatives and matched cancellation observations | Confirmation of facts, delay prerequisites, and offer timing can remain unresolved. |
| Cancellation | Recorded facts and applicable selected predicates | Complete semantic permission is not inferred from a reservation read. |
| Communication format | Parallel calls or simultaneous text and tool calls | Current-message findings remain separate from earlier departures and action eligibility. |

Table: **Audit coverage.** Full-policy permission and whole-conversation compliance remain unestablished fields in the evidence records. Checks do not use a gate's rationale as an answer key.

The live-block categories in Table \ref{tab:compact-audit} are mutually exclusive. Monitor unavailability is always separate. For substantive decisions, a known selected-predicate violation takes precedence; otherwise the accounting uses an additional supported action/prerequisite breach, then a current-message format breach, then unresolved status. Multiple findings may exist in the underlying record even though each block occupies one summary category.

The same checks cover all 231 ungated shadow proposals, including allows and the missing decision. Broad blocks comprise 36 known selected violations, eleven additional action/prerequisite breaches, four current-format-only cases, and 36 unresolved cases. Decomposed blocks comprise 34, four, one, and 18, respectively; one decision remains missing. Allowed-call cross-tabs and all supporting clauses are saved in the audit summary. These counts describe evidence categories, not complete-policy sensitivity or specificity.

Structural format departures occur in 113/181 ungated, 111/163 broad, and 102/166 decomposed reference completions. These overlapping conversation counts are not additional task failures and do not establish the permissibility of the underlying database writes. The eleven completion cases with no post-request reply are a distinct, concrete finding about a required confirmation exchange; no new primary endpoint is substituted for reference completion.

### Interpreting unresolved action permission

A full-policy judgment must distinguish forbidden, permitted, required and uncertain actions using the policy, tool schemas and prefix available at the proposal boundary. A justified block needs an identifiable policy conflict or unmet mandatory prerequisite. An unnecessary block would prevent an action supported as permitted or required with its applicable prerequisites satisfied. Unavailable facts or ambiguous policy scope can leave that distinction unresolved. Current-message format is assessed separately from action eligibility, and a prior format departure alone does not justify blocking a later valid action.

The programmatic evidence cannot settle all such judgments. In particular, selected-predicate eligibility does not establish full-policy permission, and eventual task success is not an answer key for a pre-execution decision. The paper therefore reports neither an independent agreement statistic nor a comprehensive unnecessary-block count. The 65 unresolved live blocks remain explicit rather than being assigned favorable or unfavorable labels.

## D. Artifact map and offline reproduction

\label{app:combined-artifacts}

Paths below are relative to the research artifact root. The completed compact allocation is in `intervention_study/compact_study/`. Protocol, amendment, allocation, import, and dependency files record the design and provenance. `episodes/` and `shadow/` retain original records. `native_verification.json` records replay checks; `analysis.json` contains the frozen analysis; `completion/processing_manifest.json` and `evidence/manifest.json` identify archived inputs and receipts.

The reporting directory `paper/combined_study/` contains `results_tables.json`, `results_readout.md`, the exhaustive selected shadow `case_review.json`, and the `policy_audit/` input packet. The latter preserves all public policies, schemas, prefixes, conversations, and their source mappings. Its `evidence_audit/` directory contains proposal checks, decision accounting, conversation checks, uncertainty, and exact source hashes.

Run the single reproduction command from the artifact root in the recorded research environment:

```sh
python paper/combined_study/reproduce_principal.py
```

It verifies the compact records and evidence checks, regenerates the principal tables and all paired descriptive exports, and checks exact manuscript-source regeneration. Individual checks and historical supporting-study reproduction are documented in the artifact README. The paired export and actor-specific tests are post hoc; the original four comparisons remain withheld.

These commands verify saved counts, exported inputs, boundary cases, and archive consistency without making network or model calls or changing the frozen analysis. The manuscript build records its input hashes and generates the figure from the verified results table. Compilation and artifact checks concern reproducibility of the saved evidence; they do not expand the study's policy coverage or generalization scope.

{{EARLIER_APPENDICES}}

{{EARLIER_STUDIES}}
