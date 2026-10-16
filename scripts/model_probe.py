import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GOOGLE_API_KEY", "")
candidates = [
    os.getenv("MODEL_NAME", ""),
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite-preview",
]

body = {"contents": [{"parts": [{"text": "In one sentence, what is an AI agent?"}]}]}

for name in dict.fromkeys(candidates):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent"
    start = time.time()
    try:
        r = httpx.post(url, headers={"x-goog-api-key": key}, json=body, timeout=30)
    except httpx.TimeoutException:
        print(f"{name}: TIMED OUT after {round(time.time() - start, 1)} s")
        continue
    secs = round(time.time() - start, 1)
    print(f"{name}: status {r.status_code} in {secs} s")
    if r.status_code == 200:
        data = r.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        print("   ", "".join(p.get("text", "") for p in parts)[:120])
    else:
        print("   ", r.text[:200])