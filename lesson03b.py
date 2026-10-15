import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from tools import list_terms, lookup_term
from utils import get_text

load_dotenv()


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
)

question = "Which terms do you have, and what does the first one alphabetically mean?"
result = agent.invoke({"messages": [HumanMessage(content=question)]})


print(type(result))
print(list(result.keys()))
for m in result["messages"]:
    print(type(m).__name__)
print("FINAL:", get_text(result["messages"][-1]))
print(agent.get_graph().draw_mermaid())