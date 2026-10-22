from langchain.chat_models import init_chat_model

from tutor.config import Settings, load_settings

from tutor.tools import lookup_term

def build_model(settings: Settings, name: str):
    return init_chat_model(
        name,
        model_provider=settings.model_provider,
        timeout=settings.timeout_seconds,
        max_retries=settings.max_retries,
    )


def check_model(settings: Settings, name: str) -> tuple[str | None, str | None]:
    try:
        reply = build_model(settings, name).invoke("Reply with the single word: ok")
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:150]}"
    return reply.response_metadata.get("model_name"), None


def check_tool_support(settings: Settings, name: str) -> str | None:
    try:
        reply = build_model(settings, name).bind_tools([lookup_term]).invoke(
            "What does the term 'handoff' mean? Use the glossary tool."
        )
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:150]}"
    if not reply.tool_calls:
        return "model answered without requesting the tool"
    return None

if __name__ == "__main__":
    settings = load_settings()
    names = [settings.model_name]
    if settings.fallback_model_name:
        names.append(settings.fallback_model_name)

    resolved_names = []
    for name in names:
        resolved, problem=check_model(settings, name)
        if problem:
            print(f"{name}: FAILED - {problem}")
            continue
        resolved_names.append(resolved)
        tool_problem = check_tool_support(settings, name)
        tools_status = "tools OK" if tool_problem is None else f"TOOLS PROBLEM - {tool_problem}"
        print(f"{name}: OK (served by: {resolved}) | {tools_status}")

    if len(resolved_names) != len(set(resolved_names)):
        print("WARNING: primary and fallback are served by the same model.")