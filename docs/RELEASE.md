# Public release provenance

This public repository is a clean snapshot of the verified research package accompanying **From Warnings to Interventions: Evaluating Policy Enforcement in Tool-Using LLM Agents**. Its history begins with the public artifact; the private working repository and its operational history are not imported.

## Source and changes

The source package was verified before editing against SHA-256 `1de6aee6008d509bbc7ead2ad6f7ab22550a6ee554df61238a5637cc22fa6b2b`. The original package contained 12,577 inventoried files. The public version adds a reader-facing introduction, result interpretation, reproduction guide, citation, licensing scope and offline verification.

The initial release retained scientific observations, scenario allocation, incomplete outcomes, policy judgments, analysis tables and manuscript scientific content. Two administrative JSON files omit private approval quotations and account balances. Their original and released SHA-256 values, together with the omitted field names, are recorded in `release/public_file_transformations.json`. The verification adapter first checks released bytes and then compares the original commitment against the unchanged frozen manifest. It does not claim that redacted bytes equal the originals or independently attest the withheld content.

Receipt sanitization is inherited from the source package: transport/session identifiers and optional reasoning metadata are omitted, while visible prompts, outputs, scores, arguments and usage remain. Those transformations use their own manifests. Scientific model/provider names are retained as provenance.

## Verification boundaries

[public_verification.json](../release/public_verification.json) records the current checks. The release audit examines distributed paths and text, nested receipt archives, PDF text/metadata, credential patterns, private local paths and tool-authorship attribution. It also checks the initial public commit metadata and refs. Pattern scans are scoped checks, not proof that every possible sensitive identifier is absent.

The root `SHA256SUMS.json` inventories the public files, excluding itself and the post-build public verification report. Verification output, local environments, caches and Git metadata are not part of the release. The scientific source-freeze and receipt commitments are separate and unchanged.

## Historical wording

Documentation inside the original research package may describe a private working repository, a local review candidate, pending work or a dated publication-authorization flag. Those are historical snapshots. This repository is the public distribution; public availability does not imply journal submission, acceptance or independent validation. The manuscript retains its review-format author block.

## Revision v1.1.1 — 26 October 2026

The revised manuscript separates interaction-clean conversations from clean success, clarifies study/model provenance and the two RQ1 comparison groups, adds research-question mapping, repairs appendix pointers, simplifies abstract wording, and reports costs to three decimal places. Figure 4 was already rendered with a −11 lower limit and was checked visually. The introduction identifies its initial-study example and links the compact refund example to an exact episode/native-replay record. No frozen outcomes or formal-test decisions changed.

The public review form provides the original 95 cases plus four supplementary cases needed to cover all 20 completion-loss blocks. The 65 unresolved judgments remain limitations; there are no collected human-validation results. See `review/README.md` for the amendment, response handling and separate analysis groups. Coordinator mappings and actual responses are excluded.

The [complete tagged source ZIP](https://github.com/Gaurav890/policy-gate-evaluation/archive/refs/tags/v1.1.1.zip) contains the full artifact and revised PDF. GitHub generates this archive directly from the published tag. The release's `verification-v1.1.1.json` identifies the exact downloaded ZIP hash and records a fresh-container reproduction. GitHub-generated archive hashes may change if its archive encoding changes; the per-file inventory checks payload identity. This is a GitHub supplementary package, not a claim that files have been uploaded to a journal. The public URL identifies the maintainer and is not anonymous.
