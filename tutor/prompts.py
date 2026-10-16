from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def load_prompt(name: str) -> tuple[str, str]:
    path = PROMPT_DIR / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    first_line, _, body = text.partition("\n")
    if not first_line.startswith("<!-- version:"):
        raise ValueError(f"{path.name} must start with a '<!-- version: X -->' line")
    version = first_line.removeprefix("<!-- version:").removesuffix("-->").strip()
    return version, body.strip()


if __name__ == "__main__":
    version, text = load_prompt("tutor")
    print("tutor prompt version:", version)
    print("characters:", len(text))
    print(text[:200])