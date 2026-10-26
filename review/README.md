# Independent action review

Give each reviewer only their form link and these instructions, not the paper, audit results or coordinator mapping. Use two people with relevant policy/software-security expertise; ideally at least one did not design the gates or audit. Record actual roles and experience. Do not describe author reviews as external reviews.

- [Reviewer 1 form](https://gaurav890.github.io/policy-gate-evaluation/review/#reviewer=R1)
- [Reviewer 2 form](https://gaurav890.github.io/policy-gate-evaluation/review/#reviewer=R2)
- [Downloadable offline form](../docs/review/index.html) (download the raw HTML and open it in a browser).

The form contains 99 cases, full policies, tool definitions, conversation prefixes and the fixed rubric. Current gate decisions, model identity fields, audit labels and final outcomes are not added. Earlier tool feedback can reveal interventions, so blinding is partial. The public repository contains evidence that could unblind reviewers: ask them not to browse it before returning their independent responses. A separately hosted copy of the same HTML can reduce that exposure; it cannot guarantee independence.

## Message to send with each link

> Please independently assess the proposed action in each case using the supplied policy, tools and visible conversation. Choose action permission, whether blocking would be justified, and format compliance; cite policy clauses and conversation messages for every judgment. Use “uncertain” when the evidence does not establish a conclusion. Please do not consult the paper, existing audit, another reviewer or automated judgment tools. Save checkpoints regularly. When finished, download both the CSV and submission JSON and return them privately to me. The form does not submit responses automatically. Please disclose your relevant experience and relationship to this study in the form.

## Data handling

Answers stay in that browser's local storage. Keep the same reviewer link and browser to resume; private browsing or clearing browser data may erase progress. Download a checkpoint at each break. Use Load checkpoint to move to another browser. There is no login, response server or automatic delivery. GitHub Pages serves the page under its own hosting policies; this form sends no response data to it. Do not put personal contact details in answers. Never commit returned files or coordinator mappings to this repository.

## Amendment before labeling: 26 October 2026

The original fixed sample is unchanged: 95 cases, including the census of 65 unresolved blocks and 30 sampled classified cases. Its case file SHA-256 remains `75a5447060b40cab86fcb1cc1a6d0c89377125af041ca365604dda41baa79c27`.

An audit of the completion-loss mapping found that the original packet included 16 of the 20 relevant block events. Four supplemental cases, CASE096–CASE099, add the omitted events so all 20 can receive independent judgments. They use the same rubric. No human labels had been collected when this amendment was made. The form shuffles presentation with a fixed ordering and does not mark case strata to reviewers. This is an amendment to a post hoc review, not preregistration of the experiment.

Report original-sample agreement separately from the four-case supplement. After both reviews are locked, report judgments on the 65 unresolved blocks and the 20 completion-loss blocks using the private coordinator mapping. Do not extrapolate the classified sample without its sampling weights. Disagreement or “uncertain” is not automatically an unnecessary block. Preserve original responses before any separately documented adjudication.

## Analyze returned reviews privately

Keep each `review-R1.csv` beside `review-R1-submission.json`, and likewise for R2. Then run:

```sh
python review/summarize.py /private/path/review-R1-submission.json /private/path/review-R2-submission.json --coordinator-key /private/path/coordinator-private.json > /private/path/independent-agreement.json
```

The script checks the exact packet, all 99 case IDs, valid labels, evidence fields, declarations, distinct reviewer codes and CSV/JSON agreement. It reports raw agreement, Cohen's kappa (uncertain is a category), individual counts, agreed counts and disagreements. It does not authenticate reviewer identity or invent final adjudicated classifications. Without the private key it reports only the original 95 and supplemental four groups. The historical 95-case `agreement.py` remains unchanged; do not pass it the 99-case exports.

Rebuild the self-contained form with `python review/build_form.py`; run the validation checks with `node review/test_core.js`. Packet and form hashes are in `packet_manifest.json`. Changing the packet creates a new local-storage namespace and rejects checkpoints from the old packet.
