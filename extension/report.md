# Extension findings

The original study is unchanged; its manuscript and package are archived in `submission/archive-v001/`.

- Completed **24/24 additional conversations** on **six new task IDs**, with two runs per task/instruction condition.
- **7 clean state successes**, from **3 task IDs**; 20 state successes overall. No trace editing, serialization, rejection or discarded retries.
- **3/12** repeat pairs change contract compliance; **0/12** change state success.
- Second monitor: **513/514** valid original-prefix scores; 1 missing. First-alert timing: {"at": 7, "after": 14, "no_alert": 19, "before": 7, "unidentified": 1}.
- Matched valid original prefixes: **98/510** alert disagreements. Do not treat prefixes as independent tasks.
- Extension clean-success alert counts: Gemini **1/7**; DeepSeek **5/7**. These remain proxy-relative, not full-policy error rates.
- **Human review optional:** the separate review packet is outside the reported evidence. No human labels are incorporated.
- New response-reported spend: **$2.7089**; cumulative **$15.9333**. Conservative hold **$19.9921** under the existing $30 cap.

The second monitor materially qualifies the original timing finding. More tasks and repeats do not establish family-disjoint or deployment-wide generalization. Seven clean successes are a useful denominator, not a precise estimate of a broad false-alarm rate. The later controlled eligibility cases support a separately scoped substantive-rule analysis; natural conversations remain without comprehensive semantic labels.
