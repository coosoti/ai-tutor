import json
import re
import sys
from pathlib import Path

VERBS = re.compile(
    r"\b(pass(es|ed|ing)?|transfer\w*|hand(s|ed|ing)?|take[sn]? over|taking over|"
    r"rout(e|es|ed|ing)|refer(s|red|ring)?|escalat\w*|forward(s|ed|ing)?|"
    r"redirect\w*|step\w* aside|bring\w* in)\b",
    re.IGNORECASE,
)

path = Path(sys.argv[1])
report = json.loads(path.read_text(encoding="utf-8"))
total = hits = 0
for item in report:
    for run in item["runs"]:
        turn = run["turns"][0]
        if "reply" not in turn:
            continue
        total += 1
        found = VERBS.search(turn["reply"])
        hits += bool(found)
        label = "SOLUTION VERB: " + found.group(0) if found else "none"
        print(f"{item['scenario']} run {run['run']}: {label}")
print(f"\nFirst replies containing a solution verb: {hits}/{total}")