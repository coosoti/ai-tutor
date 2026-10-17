from langchain.agents import create_agent
from langchain.agents.middleware import ModelFallbackMiddleware
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver


from tutor.config import Settings, load_settings
from tutor.models import build_model
from tutor.prompts import load_prompt
from tutor.tools import list_terms, lookup_term
from tutor.utils import get_text


def build_tutor(settings: Settings, checkpointer=None):
    _, system_prompt = load_prompt("tutor")

    middleware = []
    if settings.fallback_model_name:
        fallback_model = build_model(settings, settings.fallback_model_name)
        middleware.append(ModelFallbackMiddleware(fallback_model))

    return create_agent(
        model=build_model(settings, settings.model_name),
        tools=[list_terms, lookup_term],
        system_prompt=system_prompt,
        middleware=middleware,
        checkpointer=checkpointer,
    )

if __name__ == "__main__":
    settings = load_settings()
    version, _ = load_prompt("tutor")
    print(f"prompt v{version} | primary: {settings.model_name} | fallback: {settings.fallback_model_name}")

    agent = build_tutor(settings, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "smoke-test"}}
    result = agent.invoke(
        {"messages": [HumanMessage(content="What does handoff mean?")]},
        config=config,
    )

    messages = result["messages"]
    print("message types:", [type(m).__name__ for m in messages])
    print("REPLY:", get_text(messages[-1]))
    print("metadata:", messages[-1].response_metadata)