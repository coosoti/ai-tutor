import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from tools import list_terms, lookup_term
from utils import get_text

load_dotenv()

model = init_chat_model(
    os.getenv("MODEL_NAME"),
    model_provider="google_genai",
    timeout=30,
    max_retries=4,
)

PROMPT = "You are a glossary assistant. Use the tools to answer. Do not guess."

QUESTIONS = [
    "What does handoff mean?",
    "And what does checkpointer mean?",
    "And what does send api mean?",
    "Which of those three is mostly about saving state?",
    "Which of the three is mostly about running work in parallel?",
    "Give me a one-line summary of all three terms.",
]


def run_conversation(agent, thread_id):
    config = {"configurable": {"thread_id": thread_id}}
    for i, question in enumerate(QUESTIONS, start=1):
        result = agent.invoke({"messages": [HumanMessage(content=question)]}, config=config)
        messages = result["messages"]
        usage = messages[-1].usage_metadata or {}
        print(
            f"turn {i}: messages in state = {len(messages):2d}, "
            f"input tokens of last call = {usage.get('input_tokens')}"
        )
        if i == len(QUESTIONS):
            print("--- first message in state:", type(messages[0]).__name__)
            print(get_text(messages[0]))
            print("--- final answer:")
            print(get_text(messages[-1]))


print("=== C1: no trimming ===")
plain = create_agent(
    model=model,
    tools=[list_terms, lookup_term],
    system_prompt=PROMPT,
    checkpointer=InMemorySaver(),
)
run_conversation(plain, "plain")


print("=== C2: with summarization ===")
trimmed = create_agent(
    model=model,
    tools=[list_terms, lookup_term],
    system_prompt=PROMPT,
    checkpointer=InMemorySaver(),
    middleware=[
        SummarizationMiddleware(
            model=model,
            trigger=("messages", 8),
            keep=("messages", 4),
        )
    ],
)
run_conversation(trimmed, "trimmed")