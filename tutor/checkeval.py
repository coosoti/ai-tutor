import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path

from tutor.checker import build_checker, check_opening
from tutor.config import load_settings
from tutor.tools import GLOSSARY

LABELS = Path("evals/checker/labels.csv")
RESULTS = Path("evals/results")
HUMAN = {"L": "leak", "B": "borderline", "C": "clean"}


def load_items():
    with LABELS.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cache, items = {}, []
    for row in rows:
        if row["file"] not in cache:
            cache[row["file"]] = json.loads((RESULTS / row["file"]).read_text(encoding="utf-8"))
        scenario = next(s for s in cache[row["file"]] if s["scenario"] == row["scenario"])
        run = next(r for r in scenario["runs"] if r["run"] == int(row["run"]))
        turn = run["turns"][0]
        items.append(
            {"id": row["id"], "set": row["id"][0], "human": HUMAN[row["label"]],
             "question": turn["learner"], "draft": turn["reply"]}
        )
    return items


def judge(checker, item, reference, repeats, gap):
    votes, reasons = [], []
    for _ in range(repeats):
        try:
            verdict = check_opening(checker, item["question"], reference, item["draft"])
        except Exception as e:
            reasons.append(f"ERROR {type(e).__name__}")
            continue
        if verdict is not None:
            votes.append(verdict.label)
            reasons.append(verdict.reason)
        time.sleep(gap)
    if not votes:
        return None, 0.0, reasons
    label, count = Counter(votes).most_common(1)[0]
    return label, count / len(votes), reasons


def main():
    parser = argparse.ArgumentParser(description="Test the checker against human labels.")
    parser.add_argument("--set", choices=["A", "B"], help="only this set")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--gap", type=float, default=0.3)
    args = parser.parse_args()

    settings = load_settings()
    checker = build_checker(settings)
    reference = GLOSSARY["handoff"]
    items = [i for i in load_items() if not args.set or i["set"] == args.set]
    print(f"checker model: {settings.checker_model_name or settings.model_name} | items: {len(items)} | repeats: {args.repeats}\n")

    results = []
    for item in items:
        label, stability, reasons = judge(checker, item, reference, args.repeats, args.gap)
        results.append({**item, "checker": label, "stability": stability})
        mark = "" if label == item["human"] else "   <-- DISAGREE"
        print(f"{item['id']}  human={item['human']:<10} checker={str(label):<10} stable={stability:.2f}{mark}")
        if mark:
            print(f"      reason: {reasons[0] if reasons else '-'}")

    print("\nConfusion (human -> checker):")
    pairs = Counter((r["human"], r["checker"]) for r in results)
    for human in ("leak", "borderline", "clean"):
        row = {c: pairs[(human, c)] for c in ("leak", "borderline", "clean", None)}
        print(f"  {human:<10} leak={row['leak']} borderline={row['borderline']} clean={row['clean']} error={row[None]}")

    def count(human, flagged):
        group = [r for r in results if r["human"] == human]
        return sum(r["checker"] in flagged for r in group), len(group)

    print("\nOperating point P1 (reject only 'leak'):")
    print("  leaks caught:       %d/%d" % count("leak", ("leak",)))
    print("  borderlines caught: %d/%d" % count("borderline", ("leak",)))
    print("  clean blocked:      %d/%d" % count("clean", ("leak",)))
    print("Operating point P2 (reject 'leak' or 'borderline'):")
    print("  leaks caught:       %d/%d" % count("leak", ("leak", "borderline")))
    print("  borderlines caught: %d/%d" % count("borderline", ("leak", "borderline")))
    print("  clean blocked:      %d/%d" % count("clean", ("leak", "borderline")))
    unstable = sum(r["stability"] < 1 for r in results)
    print(f"\nUnstable items (repeats disagreed): {unstable}/{len(results)}")


if __name__ == "__main__":
    main()