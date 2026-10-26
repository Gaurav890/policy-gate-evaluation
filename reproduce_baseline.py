"""Re-run the released CPU real-trace evaluation without overwriting upstream."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "groundwork" / "baseline-source"
OUT = ROOT / "groundwork" / "baseline-reproduction"
sys.path.insert(0, str(SOURCE))


def main():
    import pandas as pd
    from derail.experiments import run_real_traces
    OUT.mkdir(exist_ok=True)
    if (OUT / "tables" / "real_traces.csv").exists():
        raise SystemExit("Reproduction output exists; refusing to overwrite")
    expected = pd.read_csv(SOURCE / "results/tables/real_traces.csv")
    run_real_traces.RESULTS = OUT
    run_real_traces.main([])
    actual = pd.read_csv(OUT / "tables/real_traces.csv")
    comparisons = []
    for _, row in actual.iterrows():
        match = expected[expected.monitor == row.monitor]
        if len(match) != 1:
            comparisons.append({"monitor": row.monitor, "status": "no_unique_reference_row"})
            continue
        differences = {column: float(row[column] - match.iloc[0][column])
                       for column in ["episode_auc", "detection_rate", "healthy_fa_rate"]}
        comparisons.append({"monitor": row.monitor, "differences": differences,
                            "match_at_1e_minus_9": all(abs(value) < 1e-9 for value in differences.values())})
    provenance = {
        "repository": "https://github.com/sunnydubey1111/agent-trajectory-sentinel",
        "revision": subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip(),
        "python": sys.version,
        "torch_available": run_real_traces._HAS_TORCH,
        "scope": "Released CPU methods on the authors' recorded healthy/injected traces; not new task data or a full-paper reproduction",
        "reference_sha256": hashlib.sha256((SOURCE / "results/tables/real_traces.csv").read_bytes()).hexdigest(),
        "comparisons": comparisons,
    }
    (OUT / "comparison.json").write_text(json.dumps(provenance, indent=2)+"\n")
    print(json.dumps(comparisons, indent=2))


if __name__ == "__main__":
    main()
