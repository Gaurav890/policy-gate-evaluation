"""Print the saved audit findings without model calls or third-party dependencies."""
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    results = json.loads((root / "replication/analysis.json").read_text())
    r = results["replication"]
    print("Saved-record audit; threshold 0.5; final expansion only")
    print(f"Completed conversations: {r['completed']}; interrupted: {len(r['incomplete'])}")
    print(f"State successes: {r['state_successes']}; interaction-clean state successes: {r['clean_successes']}")
    print("Monitor     State-success alerts      Interaction-clean success alerts")
    for model in ["gemini", "deepseek", "gptmini"]:
        cells = []
        for field in ["state_rates", "clean_rates"]:
            v = r[field][model]
            n = v["denominator"]
            cells.append(f"{v['alerts']}/{n} ({100*v['lower']:.1f}%)" if n else "Undefined (0 negatives)")
            if v["unknown"]:
                cells[-1] += f"; {v['unknown']} unknown, upper bound {100*v['upper']:.1f}%"
        print(f"{model:<12}{cells[0]:<26}{cells[1]}")
    print("The same saved alerts are compared against different negative classes.")
    print("Interaction-clean covers two format rules, not complete policy compliance.")
    print("Boundary detection is not advance prediction; scores are not calibrated probabilities.")
    print("See replication/report.md and USAGE.md for timing, eligibility cases and limitations.")


if __name__ == "__main__":
    main()
