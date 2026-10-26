# Reproducing the principal results

## Docker: one command

From the repository root:

```sh
./verify.sh
```

The script builds the pinned environment and runs checksum verification followed by `paper/combined_study/reproduce_principal.py`. Dependencies are downloaded during the image build. Execution uses `--network none`, requires no credentials and cannot make model calls.

The runtime is Python 3.13.7, NumPy 2.3.5 and Pandoc 3.8.3, on Linux ARM64. Docker Desktop on Apple Silicon supports this architecture directly. Other hosts need an ARM64 builder/runner or configured emulation. Allow several GB of working space. Output is written to `paper/combined_study/reproduced/`, which is ignored by Git.

The command verifies 1,152 live records, 384 shadow source records, 6,625 sanitized compact receipts and the 121-file source freeze. It then rederives eight compact empirical tables, three earlier main-text tables, 560 descriptive paired rows and four exploratory actor contrasts. It also verifies exact manuscript text-source regeneration. It does not rerun live collection or claim byte-identical PDF rendering.

## Existing Python environment

Use Python 3.13.7 and put Pandoc 3.8.3 on PATH:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-principal.txt
python release/verify_inventory.py
python paper/combined_study/reproduce_principal.py
```

Only dependency installation needs network access. `paper/combined_study/reproduced/reproduction.json` records checks and output hashes. Running from a fresh checkout verifies the distributed inputs before regeneration.

## Paper and earlier studies

The current paper is [paper/combined_study/manuscript.pdf](../paper/combined_study/manuscript.pdf). Its [build guide](../paper/combined_study/README.md) describes optional figure and PDF rendering. Plotting dependencies are separate in `requirements-figures.txt`; PDF compilation uses Tectonic 0.17.0.

The root `reproduce.sh` is the historical workflow, not the current principal-result entry point. Its analyses and optional native simulator replay are documented in [USAGE.md](../USAGE.md) and the historical study directories. The principal command verifies saved native-replay evidence; it does not reinstall and rerun the full simulator.

## Troubleshooting

- Docker unavailable: start Docker or use the native Python instructions.
- Architecture error: use Linux ARM64 or enable ARM64 emulation before building.
- Pandoc missing: install version 3.8.3, or use Docker.
- Checksum failure: inspect local changes and retry from a fresh checkout. Do not regenerate checksums to conceal altered evidence.
- A prospective or collection script asks for credentials: that is not the offline reproduction path. Use `./verify.sh`.

New paid experiments require separate planning, credentials and funding. They are not needed to inspect or reproduce this artifact.
