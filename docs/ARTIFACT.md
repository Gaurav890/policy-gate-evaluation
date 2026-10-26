# Evidence guide

| Location | Contents |
| --- | --- |
| `paper/combined_study/` | Current paper, result generators, tables, paired exports and verification code |
| `intervention_study/compact_study/` | Compact allocation, frozen sources, live and shadow records, completion manifest and receipt archive |
| `paper/combined_study/policy_audit/` | 392 proposal inputs, 576 nominally permitted conversations and provenance mappings |
| `paper/combined_study/policy_audit/evidence_audit/` | Programmatic full-policy evidence checks and unresolved judgments |
| `study/`, `extension/`, `replication/` | Separate earlier warning-target and timing cohorts, plus controlled cancellation experiments |
| `substantive_audit/`, `substantive_evaluation/` | Earlier policy pilot and new-task evaluation |
| `intervention_study/live_gating/` | Earlier eight-pair live-gating follow-up |
| `release/api_records_*.tar.xz` | Sanitized historical receipts; extraction and verification utilities are provided |
| `release/compact_receipt_transformations.json` | Original commitments and released hashes for compact receipts |
| `release/public_file_transformations.json` | Documented redactions of private administrative fields |
| `licenses/` | Preserved benchmark, baseline and manuscript-template notices |

The current paper integrates the studies conceptually; the cohorts keep their own denominators, designs and inference limits. Historical plans and status fields describe their recorded dates. They are not the current release status. Prospective protocols are drafts and do not represent completed experiments.

The policy-audit `coordinator_key.json` is a scientific provenance mapping, not a credential. Synthetic benchmark customers can have realistic names, addresses and contact fields. These remain part of the reproducible simulated tasks.

The distributed historical API receipts and compact receipts have distinct transformation manifests. Original byte commitments remain separate from hashes of the released bytes. See [release provenance](RELEASE.md).
