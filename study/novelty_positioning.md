# Contribution and nearest prior work

The paper is an evaluation audit of monitor targets and timing, not an adaptation algorithm. This scope replaces the initial transfer/adaptation proposal after the development observations. The locally frozen held-out allocation predates collection of its outputs; it is not an external preregistration.

The nearest prior work is Cao, Driouich and Thomas, *Beyond Task Completion: Revealing Corrupt Success in LLM Agents through Procedure-Aware Evaluation*, arXiv:2603.03116. It already establishes that task completion and procedural correctness can disagree on this benchmark family. The present paper must not claim that discovery, a first policy audit, or a new procedural taxonomy.

The narrower contribution is a fully inspectable monitor-evaluation case study: the same warnings are evaluated under explicitly different negative classes, their timing is aligned to observable proposals, and policy/target interventions use the same conversation prefix. The accounting identity is elementary. The one-call baseline is deliberately simple. The paper's value depends on the clarity and reproducibility of the evaluation diagnosis, not a new mathematical estimator or state-of-the-art detector.

Other primary sources cited in the manuscript cover online warning representations (PrefixGuard), telemetry monitoring and deployment refitting (Real-Time Detection and Repair), repeated reliability stress testing (ReliabilityBench), retrospective diagnosis (AgentRx), and controlled tool-fault replay (AgentCheck). Only seven CPU baseline rows on the external authors' data were reproduced locally. No performance comparison to those methods on our held-out records is implied.

Likely reviewer concerns are the small number of task IDs, shared workflow families, a narrow and sometimes low-severity contract, one monitor model, unseeded mutable hosted models, and incremental distinction from procedure-aware evaluation. These are substantive limitations. The manuscript states them directly and does not infer comprehensive policy compliance, calibrated failure probabilities, prevented harm, or general adaptation superiority.

Primary references and retrieved metadata are in `paper/references.bib` and `paper/reference_metadata.json`. The title, abstract and claims must continue to describe the measured audit if the paper is revised.
