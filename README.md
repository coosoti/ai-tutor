# AI Tutor

A command-line tutor that asks questions and gives hints instead of answers.

## Setup
1. Install uv, then run: uv sync
2. Copy .env.example to .env and fill in your keys (never commit .env).
3. Check the models: uv run python -m tutor.models

## Run
- Chat: uv run python -m tutor --thread my-session
- Tests: uv run python -m pytest -q
- Evaluate: MAX_RETRIES=2 uv run python -m tutor.evalrun --runs 3 --gap 3
- Re-grade a saved run: uv run python -m tutor.regrade evals/results/<file>.json