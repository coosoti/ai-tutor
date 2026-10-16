import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

from utils import get_text

load_dotenv()

GLOSSARY = {
    "send api": "A LangGraph feature that lets one node fan out work to a dynamic number of parallel workers, each with its own input.",
    "handoff": "A multi-agent pattern where agents pass control to each other, and any agent can reply directly to the user.",
    "checkpointer": "A component that saves a graph's state after each step so a conversation can continue later under the same thread ID.",
}

@tool
def lookup_term(term: str) -> str:
    """Look up the definition of an agentic AI term in the course glossary.
    Use this whenever the learner asks what a specific term means."""
    print("[tool ran] term =", repr(term))
    return GLOSSARY.get(term.lower().strip(), f"No glossary entry for '{term}'.")
    

# print("=== Part A: the tool is just a function ===")
# print(type(lookup_term))
# print(lookup_term.name)
# print(lookup_term.description)
# print(lookup_term.args)
# print(lookup_term.invoke({"term": "Send API"}))

model = init_chat_model(
    os.getenv("MODEL_NAME"),
    model_provider="google_genai",
    timeout=30,
    max_retries=1,
)
model_with_tools = model.bind_tools([lookup_term])

# print("=== Part B1: a question that needs the tool ===")
# r1 = model_with_tools.invoke("What does the Send API mean?")
# print("text:", repr(get_text(r1)))
# print("tool_calls:", r1.tool_calls)

# print("=== Part B2: a question that does not ===")
# r2 = model_with_tools.invoke("Say hello in five words.")
# print("text:", repr(get_text(r2)))
# print("tool_calls:", r2.tool_calls)

# print("=== Part B3: a question that does not ===")
# r3 = model_with_tools.invoke("What is the definition of SEND API?")
# print("text:", repr(get_text(r3)))
# print("tool_calls:", r3.tool_calls)

print("=== Part C: Close the loop ===")
messages = [
    SystemMessage(
        content="You are a patient tutor. Never give the answer directly. "
        "Ask one guiding question instead."
    ),
    HumanMessage(content="What does the Send API mean?"),
]

ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

for call in ai_msg.tool_calls:
    output = lookup_term.invoke(call["args"])
    messages.append(ToolMessage(content=output, tool_call_id=call["id"]))

print("messages so far: ", [type(m).__name__ for m in messages])

final = model_with_tools.invoke(messages)
messages.append(final)

print("final text:", get_text(final))
print("final tool_calls:", final.tool_calls)
print(final.usage_metadata)