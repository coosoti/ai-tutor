import json
import sys
from pathlib import Path

import yaml

from tutor.evalrun import SCENARIO_FILE, evaluate, summarize


def main():
    files = sorted(Path("evals/results").glob("*.json"))
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else files[-1]
    print("re-grading:", path.name)

    scenarios = {s["id"]: s for s in yaml.safe_load(SCENARIO_FILE.read_text(encoding="utf-8"))}
    report = json.loads(path.read_text(encoding="utf-8"))

    hard_failing = 0
    for item in report:
        scenario = scenarios[item["scenario"]]
        graded = [g for g in (evaluate(scenario, run) for run in item["runs"]) if g is not None]
        print(f"\n{item['scenario']} (graded runs: {len(graded)}/{len(item['runs'])})")
        rows = summarize(graded) if graded else []
        for name, kind, passes, total, ok in rows:
            print(f"  {name:<28} {kind:<5} {passes}/{total}  {'pass' if ok else 'FAIL'}")
            hard_failing += int(kind == "hard" and not ok)
    print(f"\nHard checks failing: {hard_failing}")


if __name__ == "__main__":
    main()