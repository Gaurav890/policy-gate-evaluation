# Reproduced principal tables

```{=latex}
\begin{table}[htbp]\centering\small
\caption{Live outcomes. Each panel contains 192 assignments per condition. Unresolved outcomes remain in denominators.}\label{tab:compact-live}
\begin{tabular}{lrrr}\toprule Condition & Positive / assigned & Unresolved & Assignment bounds (\%)\\\midrule
\multicolumn{4}{l}{\textbf{A. Pressure: executed violation}}\\
No gate & 21/192 & 0 & 10.94--10.94\\
Broad & 1/192 & 2 & 0.52--1.56\\
Decomposed & 2/192 & 1 & 1.04--1.56\\
\midrule
\multicolumn{4}{l}{\textbf{B. Permitted: reference completion}}\\
No gate & 181/192 & 0 & 94.27--94.27\\
Broad & 163/192 & 2 & 84.90--85.94\\
Decomposed & 166/192 & 3 & 86.46--88.02\\
\midrule
\end{tabular}\end{table}
```

| Mechanical proposal class | Proposals | Supporting pairs / 32 | Broad blocks | Decomposed blocks |
| :--- | ---: | ---: | ---: | ---: |
| State-changing covered violation | 21 | 13 | 21/21 | 20/21 |
| Violation already rejected natively | 15 | 7 | 15/15 | 14/15 |
| Selected-eligible, public evidence sufficient | 99 | 22 | 17/99 | 0/99 |
| Selected-eligible, private facts needed | 96 | 26 | 34/96 | 23/96* |

Table: **Decisions on identical ungated writes.** Supporting pairs overlap across classes. *One decomposed decision is missing in the 96-proposal class. All broad decisions are observed. \label{tab:compact-shadow}

| Native classification of a live blocked write | Broad | Decomposed |
| :--- | ---: | ---: |
| State-changing covered violation | 26 | 22 |
| Covered violation already rejected by the tool | 13 | 13 |
| Selected-eligible, public evidence sufficient | 26 | 0 |
| Selected-eligible, private facts needed | 36 | 23 |
| Monitor unavailable | 1 | 1 |
| **All blocked writes** | **102** | **59** |

Table: **Native replay of live blocks.** Counts are events on condition-dependent trajectories. \label{tab:compact-blocks}

| Evidence category for the blocked event | Broad | Decomposed |
| :--- | ---: | ---: |
| Known selected-predicate violation | 39 | 35 |
| Additional supported action/prerequisite breach | 7 | 3 |
| Current-message format breach only | 10 | 0 |
| Full-policy status unresolved | 45 | 20 |
| Monitor unavailable | 1 | 1 |
| **All blocked writes** | **102** | **59** |

Table: **Programmatic evidence for live blocks.** The 74 selected-predicate violations include the 26 natively rejected calls in Table \ref{tab:compact-blocks}. Evidence for a policy objection and additional prevention of a database change are different measurements. Formatting objections concern the current message, not necessarily the eligibility of the underlying action. \label{tab:compact-audit}

| Actor | Violation: broad | Violation: decomp. | Completion: broad | Completion: decomp. |
| :--- | ---: | ---: | ---: | ---: |
| DeepSeek V4.1 Flash | [+0.00, +1.56] | +0.00 | [-1.56, +0.00] | [-4.69, -1.56] |
| GPT-5.4 Mini | -31.25 | -29.69 | -23.44 | -17.19 |
| Claude Opus 5.5 | [+0.00, +1.56] | [+0.00, +1.56] | [-3.12, -1.56] | [-1.56, +0.00] |

Table: **Paired gate-minus-ungated differences by actor (percentage points).** A single value is the descriptive estimate with fully observed outcomes; brackets give finite-assignment bounds when values are missing. Violation contrasts use pressure requests and completion contrasts use nominally permitted requests. \label{tab:paired-actors}

| Rule | Violation: broad | Violation: decomp. | Completion: broad | Completion: decomp. |
| :--- | ---: | ---: | ---: | ---: |
| Basic economy | -4.17 | +4.17 | [-20.83, -16.67] | -8.33 |
| Cancellation | [-4.17, +0.00] | -4.17 | [-16.67, -12.50] | +0.00 |
| Compensation | -29.17 | -29.17 | -12.50 | -25.00 |
| Passenger count | [+0.00, +4.17] | +0.00 | -8.33 | -4.17 |
| Customer lookup | -25.00 | [-29.17, -25.00] | -4.17 | +0.00 |
| Further item change | -20.83 | -20.83 | -4.17 | -8.33 |
| Refund destination | +0.00 | +0.00 | -8.33 | [-12.50, -4.17] |
| Delivered return | +0.00 | +0.00 | +0.00 | [-4.17, +0.00] |

Table: **Paired gate-minus-ungated differences by rule (percentage points).** A single value is the descriptive estimate with fully observed outcomes; brackets give finite-assignment bounds when values are missing. Violation contrasts use pressure requests and completion contrasts use nominally permitted requests. \label{tab:paired-rules}

| Gate | Losses | With block | No block | Gains | Unresolved |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Broad | 16 | 11 | 5 | 0 | 2 |
| Decomposed | 18 | 9 | 9 | 6 | 3 |

Table: **Matched permitted-task completion changes.** Each gate is matched to 192 ungated assignments. A loss requires both outcomes to be observed. Block presence is an association, not attribution. \label{tab:completion-losses}

| Outcome | Gate | Discordant b/c | Nominal exact p | Context Holm p |
| :--- | ---: | ---: | ---: | ---: |
| Violation | Broad | 20/0 | 1.90735e-06 | 0.00195312 |
| Violation | Decomposed | 20/1 | 2.09808e-05 | 0.00585938 |
| Completion | Broad | 15/0 | 6.10352e-05 | 0.00292969 |
| Completion | Decomposed | 17/6 | 0.0346897 | 0.0415039 |

Table: **Unplanned GPT-5.4 Mini analysis.** Sixty-four matched runs per contrast. Context sensitivity keeps linked scenarios and repeats together in 31 groups; Holm correction covers four tests. Post hoc selection remains uncorrected. \label{tab:exploratory-tests}
