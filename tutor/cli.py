import argparse
import sqlite3
import time
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from tutor.agent import build_tutor
from tutor.config import load_settings
from tutor.models import check_model
from tutor.prompts import load_prompt
from tutor.utils import get_text

HELP = "Commands: /help /retry /quit (anything else goes to the tutor)"


def parse_args():
    parser = argparse.ArgumentParser(description="Chat with AI tutor.")
    parser.add_argument(
        "--thread",
        default="default",
        help="session name; the same name resumes the same conversation",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="test the primary and fallback models before starting",
    )
    return parser.parse_args()


def saved_messages(agent, config):
    snapshot = agent.get_state(config)
    return snapshot, snapshot.values.get("messages", [])


def run_turn(agent, config, user_input):
    _, before = saved_messages(agent, config)
    start = time.perf_counter()
    payload = {"messages": [HumanMessage(content=user_input)]} if user_input else None
    result = agent.invoke(payload, config=config)
    seconds = time.perf_counter() - start

    new = result["messages"][len(before):]
    ai_messages = [m for m in new if isinstance(m, AIMessage)]
    tokens_in = sum((m.usage_metadata or {}).get("input_tokens", 0) for m in ai_messages)
    tokens_out = sum((m.usage_metadata or {}).get("output_tokens", 0) for m in ai_messages)
    served_by = "?"
    if ai_messages:
        served_by = ai_messages[-1].response_metadata.get("model_name", "?")

    print(f"\ntutor> {get_text(result['messages'][-1])}\n")
    print(
        f"  [{served_by} | {len(ai_messages)} model call(s) | "
        f"tokens in/out: {tokens_in}/{tokens_out} | {seconds:.1f}s]\n"
    )


def check_models(settings):
    names = [settings.model_name]
    if settings.fallback_model_name:
        names.append(settings.fallback_model_name)
    for name in names:
        resolved, problem = check_model(settings, name)
        if problem:
            print(f"  {name}: FAILED - {problem}")
        else:
            print(f"  {name}: OK (served by {resolved})")


def main():
    args = parse_args()
    settings = load_settings()

    if args.check:
        check_models(settings)

    db_file = Path(settings.db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file, check_same_thread=False)
    agent = build_tutor(settings, checkpointer=SqliteSaver(conn))
    version, _ = load_prompt("tutor")
    config = {
        "configurable": {"thread_id": args.thread},
        "run_name": "tutor-turn",
        "tags": ["m1", "cli"],
        "metadata": {
            "prompt_version": version,
            "primary_model": settings.model_name,
            "fallback_model": settings.fallback_model_name,
            "session_id": args.thread,
        },
    }

    _, history = saved_messages(agent, config)
    tracing = f"ON (project {settings.tracing_project})" if settings.tracing_enabled else "off"
    print(f"AI Tutor | prompt v{version} | model: {settings.model_name} | session: {args.thread}")
    print(f"Tracing: {tracing}")
    if history:
        print(f"Resuming: {len(history)} saved messages in this session.")
    else:
        print("New session.")
    print(HELP + "\n")

    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not text:
            continue
        if text == "/quit":
            print("Bye.")
            break
        if text == "/help":
            print(HELP)
            continue
        try:
            if text == "/retry":
                if not agent.get_state(config).next:
                    print("Nothing to retry.\n")
                    continue
                run_turn(agent, config, None)
            else:
                run_turn(agent, config, text)
        except Exception as e:
            print(f"\n[problem] The tutor could not answer ({type(e).__name__}).")
            print(f"          Detail: {str(e)[:150]}")
            print("          Type /retry to resume the interrupted turn.\n")
