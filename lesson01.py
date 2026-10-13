import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from utils import get_text

load_dotenv()

model = init_chat_model(
    os.getenv("MODEL_NAME"),
    model_provider="google_genai",
)

print("Sending request...")
response = model.invoke("In one sentence, what is an AI agent?")

print(type(response))
print(get_text(response))
print(response.usage_metadata)

messages = [
    SystemMessage(
        content="You are a patient tutor. Never give the answer directly."
        "Ask one guiding question instead."
    ),
    HumanMessage(content="What does the Send API do in LangGraph?")
]

response2 = model.invoke(messages)
print("--- Experiment 2 ---")
print(get_text(response2))
print(response2.usage_metadata)

no_memory = model.invoke("What did I just ask you?")
print("--- Experiment 3q: no history ---")
print(get_text(no_memory))
print(no_memory.usage_metadata)
history = messages + [response2, HumanMessage(content="What did I just ask you?")]
with_memory = model.invoke(history)

print("--- Experiment 3b: With history ---")
print(get_text(with_memory))
print(with_memory.usage_metadata)