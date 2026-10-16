import os

from dotenv import load_dotenv
from langchain.agents import create_agent
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
    max_retries=1,
)

PROMPT = "You are a glossary assistant. Use the tools to answer. Do not guess."


def ask(agent, text, thread_id=None):
    config = {"configurable": {"thread_id": thread_id}} if thread_id else None
    result = agent.invoke({"messages": [HumanMessage(content=text)]}, config=config)
    messages = result["messages"]
    print(f" (messages in state: {len(messages)})")
    return get_text(messages[-1])


print("=== A1: agent WITHOUT a checkpointer ===")
agent1 = create_agent(model=model, tools=[list_terms, lookup_term], system_prompt=PROMPT)
print(ask(agent1, "What does handoff mean?"))
print(ask(agent1, "Which term did I just ask about?"))

print("=== A2: agent WITH a checkpinter, thread 'a' ===")
agent2 = create_agent(
    model=model,
    tools=[list_terms, lookup_term],
    system_prompt=PROMPT,
    checkpointer=InMemorySaver(),
)
print(ask(agent2, "What does handoff mean?", thread_id="a"))
print(ask(agent2, "Which term did I just ask about?", thread_id="a"))

print("=== A3: same agent, a DIFFERENT thread 'b' ===")
print(ask(agent2, "Which term did I just ask about?", thread_id="b"))