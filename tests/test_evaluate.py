from tutor.evalrun import evaluate

SCENARIO = {
    "id": "T",
    "checks": [
        {"turn": 1, "tool_required": True, "required_any": ["alpha"], "ends_with_question": True}
    ],
}


def make_run(tool_used):
    return {"turns": [{"learner": "q", "reply": "alpha?", "seconds": 1.0, "tool_used": tool_used}]}


def test_each_check_appears_once():
    names = [name for name, _, _ in evaluate(SCENARIO, make_run(True))]
    assert len(names) == len(set(names)), names


def test_missing_tool_use_is_a_hard_failure():
    results = evaluate(SCENARIO, make_run(False))
    tool = [(kind, ok) for name, kind, ok in results if name == "T1:tool_used"]
    assert tool == [("hard", False)]