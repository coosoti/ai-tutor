import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from tools import list_terms, lookup_term
from utils import get_text


load_dotenv()

model = init_chat_model(
    os.getenv("MODEL_NAME"),
    model_provider="google_genai",
    timeout=30,
    max_retries=1,
)
TOOLS = [list_terms, lookup_term]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}
model_with_tools = model.bind_tools(TOOLS)

MAX_STEPS = 5

def run_agent(messages):
    for step in range(MAX_STEPS):
        ai_msg = model_with_tools.invoke(messages)
        messages.append(ai_msg)
        print(f"[step {step + 1}] tool requests:", [c["name"] for c in ai_msg.tool_calls])

        if not ai_msg.tool_calls:
            return ai_msg

        for call in ai_msg.tool_calls:
            tool_fn = TOOLS_BY_NAME.get(call["name"])
            if tool_fn is None:
                output = f"Error: there is no tool name {call['name']}."
            else:
                try:
                    output = tool_fn.invoke(call["args"])
                except Exception as e:
                    output = f"Error: {e}"
            messages.append(ToolMessage(content=output, tool_call_id=call["id"]))
    raise RuntimeError(f"Agent did not finish within {MAX_STEPS} steps")


messages = [
    SystemMessage(content="You are a glossary assistant. Use the tools to answer. Do not guess."),
    HumanMessage(content="Which terms do you have, and what does the first one alphabetically mean?"),
]

final = run_agent(messages)
print("FINAL:", get_text(final))
print("total messages:", len(messages))


total_in = 0
total_out = 0
for i, m in enumerate(messages):
    usage = getattr(m, "usage_metadata", None)
    if usage:
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        print(f"message {i}: input={usage['input_tokens']} output={usage['output_tokens']}")
print("TOTAL input:", total_in, "output:", total_out)