import json
import sys
from pathlib import Path

files = sorted(Path("evals/results").glob("*.json"))
if not files:
    sys.exit("No result files yet.")
path = files[-1]
wanted = sys.argv[1] if len(sys.argv) > 1 else None
print("file:", path.name)

for item in json.loads(path.read_text(encoding="utf-8")):
    if wanted and item["scenario"] != wanted:
        continue
    for run in item["runs"]:
        print(f"\n--- {item['scenario']} run {run['run']} ---")
        for turn in run["turns"]:
            print("learner>", turn["learner"])
            if "error" in turn:
                print("  ERROR:", turn["error"])
            else:
                print("tutor>  ", turn["reply"])