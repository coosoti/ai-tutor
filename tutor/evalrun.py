import argparse
import json
import math
import re
import statistics
import time
import uuid
from datetime import datetime
from pathlib import Path

import yaml
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from tutor.agent import build_tutor
from tutor.config import load_settings
from tutor.models import check_model, check_tool_support
from tutor.prompts import load_prompt
from tutor.utils import get_text


SCENARIO_FILE = Path("evals/scenarios.yaml")
RESULTS_DIR = Path("evals/results")
PRAISE = re.compile(
    r"^\W*(great|excellent|good (question|point)|nice|awesome|fantastic|wonderful)\b",
    re.IGNORECASE,
)

GENERAL_CHECKS = [
    ("max_120_words", "soft", lambda r: len(r.split()) <= 120),
    ("one_question", "soft", lambda r: r.count("?") == 1),
    ("no_praise_opener", "soft", lambda r: not PRAISE.match(r)),
]

def run_scenario(settings, scenario, run_no, version):
    agent = build_tutor(settings, checkpointer=InMemorySaver())
    thread_id = f"eval-{scenario['id']}-{run_no}-{uuid.uuid4().hex[:6]}"
    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": "eval-turn",
        "tags": ["eval", scenario["id"]],
        "metadata": {
            "prompt_version": version,
            "primary_model": settings.model_name,
            "fallback_model": settings.fallback_model_name,
            "scenario": scenario["id"],
            "run_no": run_no,
        },
    }
    turns = []
    seen = 0
    for text in scenario["learner_turns"]:
        start = time.perf_counter()
        try:
            result = agent.invoke({"messages": [HumanMessage(content=text)]}, config=config)
        except Exception as e:
            turns.append({"learner": text, "error": f"{type(e).__name__}: {str(e)[:300]}"})
            break
        seconds = time.perf_counter() - start
        new = result["messages"][seen:]
        seen = len(result["messages"])
        ai = [m for m in new if isinstance(m, AIMessage)]
        turns.append(
            {
                "learner": text,
                "reply": get_text(result["messages"][-1]),
                "seconds": round(seconds, 2),
                "model": ai[-1].response_metadata.get("model_name", "?") if ai else "?",
                "model_calls": len(ai),
                "tool_used": any(isinstance(m, ToolMessage) for m in new),
                "tokens_in": sum((m.usage_metadata or {}).get("input_tokens", 0) for m in ai),
                "tokens_out": sum((m.usage_metadata or {}).get("output_tokens", 0) for m in ai)

            }
        )
    return {"run": run_no, "thread_id": thread_id, "turns": turns}


def specific_checks(reply, spec):
    low = reply.lower()
    out = []
    if "forbidden_phrases" in spec:
        hits = [p for p in spec["forbidden_phrases"] if re.search(p, low)]
        out.append(("no_leak_phrases", "hard", not hits))
    if "must_not_start_with" in spec:
        bad = any(low.lstrip().startswith(p.lower()) for p in spec["must_not_start_with"])
        out.append(("no_bare_confirmation", "hard", not bad))
    if "required_any" in spec:
        out.append(("mentions_expected_idea", "soft", any(p.lower() in low for p in spec["required_any"])))
    if spec.get("ends_with_question"):
        out.append(("ends_with_question", "soft", reply.rstrip().endswith("?")))
    return out


def run_with_retries(settings, scenario, run_no, version, attempts=3, pause=15):
    for attempt in range(1, attempts + 1):
        run = run_scenario(settings, scenario, run_no, version)
        run["attempts"] = attempt
        if not any("error" in turn for turn in run["turns"]):
            return run
        print(f"   attempt {attempt}/{attempts} hit on API error; pausing {pause}s")
        time.sleep(pause)
    return run
    

def evaluate(scenario, run):
    if any("error" in turn for turn in run["turns"]):
        return None
    specs = {c["turn"]: c for c in scenario.get("checks", [])}
    results = []
    replies = []
    for i, turn in enumerate(run["turns"], start=1):
        replies.append(turn["reply"])
        for name, kind, fn in GENERAL_CHECKS:
            results.append((f"T{i}:{name}", kind, fn(turn["reply"])))
        if i in specs:
            for name, kind, ok in specific_checks(turn["reply"], specs[i]):
                if specs[i].get("tool_required"):
                    results.append((f"T{i}:tool_used", "hard", turn.get("tool_used", False)))
                results.append((f"T{i}:{name}", kind, ok))
    if scenario.get("no_duplicate_replies"):
        results.append(("no_duplicate_replies", "soft", len(set(replies)) == len(replies)))
    return results


def summarize(all_results):
    table = {}
    for results in all_results:
        for name, kind, ok in results:
            entry = table.setdefault(name, {"kind": kind, "passes": 0})
            entry["passes"] += int(ok)
    total = len(all_results)
    rows = []
    for name, entry in table.items():
        needed = total if entry["kind"] == "hard" else math.ceil(2 * total / 3)
        rows.append((name, entry["kind"], entry["passes"], total, entry["passes"] >= needed))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Run scripted tutor conversations.")
    parser.add_argument("--runs", type=int, default=3, help="runs per scenario")
    parser.add_argument("--scenario", help="run only the scenario with this id")
    parser.add_argument("--show", action="store_true", help="print full transcripts")
    parser.add_argument("--gap", type=float, default=0, help="seconds to wait between runs")
    args = parser.parse_args()

    settings = load_settings()
    version, _ = load_prompt("tutor")
    print(
        f"prompt v{version} | primary {settings.model_name} | "
        f"fallback {settings.fallback_model_name} | runs {args.runs} | "
        f"timeout {settings.timeout_seconds}s | retries {settings.max_retries}"
    )

    for name in filter(None, [settings.model_name, settings.fallback_model_name]):
        _, problem = check_model(settings, name)
        problem = problem or check_tool_support(settings, name)
        if problem:
            print(f"Health check FAILED for {name}: {problem}")
            raise SystemExit(1)
    print("Health check passed for both models.\n")

    scenarios = yaml.safe_load(SCENARIO_FILE.read_text(encoding="utf-8"))
    if args.scenario:
        scenarios = [s for s in scenarios if s["id"] == args.scenario]

    seconds_all = []
    report = []
    api_failures = 0
    total_runs = 0
    checks_passed = checks_failed = 0

    for scenario in scenarios:
        runs, valid_results = [], []
        for run_no in range(1, args.runs + 1):
            run = run_with_retries(settings, scenario, run_no, version)
            runs.append(run)
            total_runs += 1
            graded = evaluate(scenario, run)
            if graded is None:
                api_failures += 1
            else:
                valid_results.append(graded)
            seconds_all += [t["seconds"] for t in run["turns"] if "seconds" in t]
            status = "done" if graded is not None else "FAILED (API error)"
            print(f"  {scenario['id']} run {run_no}/{args.runs} {status}, attempts used: {run['attempts']}")
            time.sleep(args.gap)

        if args.show:
            for run in runs:
                print(f"\n--- {scenario['id']} run {run['run']} ---")
                for t in run["turns"]:
                    print(f"learner> {t['learner']}")
                    if "error" in t:
                        print(f"  ERROR: {t['error']}")
                    else:
                        print(f"tutor>   {t['reply']}")
                        print(f"  [{t['model']} | {t['seconds']}s | tool: {t['tool_used']}]")

        if not valid_results:
            print(f"\n{scenario['id']}: NO VALID RUNS, cannot grade\n")
            report.append({"scenario": scenario["id"], "rows": [], "runs": runs})
            continue

        rows = summarize(valid_results)
        print(f"\n{scenario['id']} (graded runs: {len(valid_results)}/{args.runs})")
        for name, kind, passes, total, ok in rows:
            print(f"  {name:<28} {kind:<5} {passes}/{total}  {'pass' if ok else 'FAIL'}")
            checks_passed += int(ok)
            checks_failed += int(not ok)
        report.append({"scenario": scenario["id"], "rows": rows, "runs": runs})
        print()

    print(f"Runs graded: {total_runs - api_failures}/{total_runs} | API failures after retries: {api_failures}")
    print(f"Checks passed: {checks_passed} | failed: {checks_failed}")
    if seconds_all:
        print(
            f"Latency per turn: median {statistics.median(seconds_all):.1f}s | "
            f"max {max(seconds_all):.1f}s | turns {len(seconds_all)}"
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out = RESULTS_DIR / f"{stamp}_v{version}_{settings.model_name}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()