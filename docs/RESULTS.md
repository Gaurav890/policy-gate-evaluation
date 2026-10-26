# Results and interpretation

The compact intervention study is the primary evaluation. Earlier warning-target, timing and cancellation cohorts provide separate supporting evidence; their sample sizes must not be pooled with the compact allocation.

## Study allocation

32 designed scenario pairs × three actors × two repetitions × two request types × three live conditions = 1,152 assignments. There are 1,143 normally completed conversations, eight infrastructure interruptions and one customer-turn-limit outcome. Shadow scoring covers 384 ungated sources: 383 complete and one with missing subsequent monitor output. Missing observations have not been retried or replaced in this release.

The broad gate uses a full-policy model judgment. The decomposed gate combines selected public-evidence predicates with focused model questions. Their policy coverage and decision structure differ, so these results are not a controlled comparison of architectures alone.

## Assigned-outcome bounds

| Outcome | No gate | Broad gate | Decomposed gate |
| --- | ---: | ---: | ---: |
| Pressure: executed covered violation | 10.94% | 0.52–1.56% | 1.04–1.56% |
| Permitted: reference completion | 94.27% | 84.90–85.94% | 86.46–88.02% |

Each denominator is 192. Bounds assign every unresolved binary outcome to either possible value; they are **not confidence intervals**. Counts and calculations appear in [principal tables](../paper/combined_study/principal_tables.md).

## Why block counts are insufficient

The broad gate blocked 102 writes and the decomposed gate blocked 59. Native replay identifies 48 blocked writes that would cause a covered violating state change, and 26 that the tools would already reject. These are event counts on different live trajectories, not counts of independently saved tasks.

The programmatic audit retains 65 unresolved full-policy judgments. A call that passes selected executable rules may still breach another policy. Consequently, neither the raw block count nor lower reference completion estimates an unnecessary-block rate.

Matched permitted-task comparisons show 16 completion losses with the broad gate and 18 with the decomposed gate; respectively 11 and nine co-occur with a block. The decomposed condition also has six completion gains. Co-occurrence does not attribute a task failure to a particular block.

## Boundaries of the conclusion

- All 21 ungated executed violations arise from GPT-5.4 Mini. The other two actors have zero observed ungated violations in this allocation. This limits evidence of improvement across actors.
- The 32 pairs are designed cases, not a representative sample of all agent workflows.
- The study scope changed after collection began. Four planned formal tests remain withheld under the missingness rule.
- Four added actor-specific contrasts are post hoc and exploratory. Their reported adjustments do not correct for choosing that actor after seeing the results.
- Native replay checks immediate tool consequences. Reference-state completion does not certify procedural or full-policy compliance.
- Hosted model identifiers and unseeded sampling do not promise identical new live trajectories.

The supported contribution is a way to distinguish warning detection, added transition protection and downstream task outcomes, demonstrated by reproducible disagreements between those measurements.
