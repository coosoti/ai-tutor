from langchain.chat_models import init_chat_model

from tutor.config import Settings, load_settings


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


if __name__ == "__main__":
    settings = load_settings()
    names = [settings.model_name]
    if settings.fallback_model_name:
        names.append(settings.fallback_model_name)
    for name in names:
        resolved, problem=check_model(settings, name)
        if problem:
            print(f"{name}: FAILED - {problem}")
        else:
            print(f"{name}: OK (Served by: {resolved})")