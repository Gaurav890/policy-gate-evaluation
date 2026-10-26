#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
docker build --platform linux/arm64 -t policy-gate-reproduction:1.0.0 .
docker run --rm --network none --platform linux/arm64   -e PYTHONDONTWRITEBYTECODE=1   -v "$PWD":/artifact -w /artifact   policy-gate-reproduction:1.0.0   sh -c 'python release/verify_inventory.py && python paper/combined_study/reproduce_principal.py'
