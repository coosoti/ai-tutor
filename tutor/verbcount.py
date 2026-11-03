import json
import sys
from pathlib import Path

from tutor.solution_verbs import find_solution_verb


def main():
    path = Path(sys.argv[1])
    report = json.loads(path.read_text(encoding="utf-8"))
    total = hits = 0
    for item in report:
        for run in item["runs"]:
            turn = run["turns"][0]
            if "reply" not in turn:
                continue
            total += 1
            found = find_solution_verb(turn["reply"])
            hits += bool(found)
            print(f"{item['scenario']} run {run['run']}: {found or 'none'}")
    print(f"\nFirst replies containing a solution verb: {hits}/{total}")


if __name__ == "__main__":
    main()