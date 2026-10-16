import os
import sqlite3
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from tools import list_terms, lookup_term
from utils import get_text


load_dotenv()

if len(sys.argv) < 2:
    print('Usage: uv run python lesson04b.py "your question"')
    sys.exit(1)


os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/tutor_memory.db", check_same_thread=False)
saver = SqliteSaver(conn)

model = init_chat_model(
    os.getenv("MODEL_NAME"),
    model_provider="google_genai",
    timeout=30,
    max_retries=1,
)

agent = create_agent(
    model=model,
    tools=[list_terms, lookup_term],
    system_prompt="You are a glossary assistant. Use the tools to answer. Do not guess.",
    checkpointer=saver,
)

config = {"configurable": {"thread_id": "study-1"}}
result = agent.invoke({"messages": [HumanMessage(content=sys.argv[1])]}, config=config)

print("messages in state:", len(result["messages"]))
print(get_text(result["messages"][-1]))