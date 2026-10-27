from pathlib import Path

import yaml

from tutor.evalrun import specific_checks

SCENARIOS = yaml.safe_load(Path("evals/scenarios.yaml").read_text(encoding="utf-8"))
S1_SPEC = SCENARIOS[0]["checks"][0]

LEAKS = [
    "How do you think one agent decides to pass control of the conversation over to another agent?",
    "How do you think one agent decides it is time to pass the work to a different agent?",
    "How might one agent pass control or ongoing work to another agent?",
    "When one agent finishes its task and transfers control to another specialized agent, how does the receiver know what to do?",
]

CLEAN = [
    "Imagine a support bot that cannot fix a billing issue. What do you expect should happen next, and who should speak to the customer?",
    "Suppose three specialized agents share one conversation. What problems could appear if each tried to answer at once?",
    "In a system where different specialized agents handle different tasks, what could go wrong if two of them disagree?",
]


def leak_check_passed(reply):
    results = {name: ok for name, _, ok in specific_checks(reply, S1_SPEC)}
    return results["no_leak_phrases"]


def test_known_leaks_are_caught():
    for reply in LEAKS:
        assert not leak_check_passed(reply), reply


def test_clean_replies_pass():
    for reply in CLEAN:
        assert leak_check_passed(reply), reply