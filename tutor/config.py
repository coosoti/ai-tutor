import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    model_name: str
    fallback_model_name: str | None
    model_provider: str
    db_path: str
    max_retries: int
    timeout_seconds: int


def load_settings() -> Settings:
    model_name = os.getenv("MODEL_NAME")
    if not model_name:
        raise RuntimeError("MODEL_NAME is not set. Add it to your .env file.")
    return Settings(
        model_name=model_name,
        fallback_model_name=os.getenv("FALLBACK_MODEL_NAME") or None,
        model_provider=os.getenv("MODEL_PROVIDER", "google_genai"),
        db_path=os.getenv("DB_PATH", "data/tutor_memory.db"),
        max_retries=int(os.getenv("MAX_RETRIES", "1")),
        timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
    )


if __name__ == "__main__":
    print(load_settings())