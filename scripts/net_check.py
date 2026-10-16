import os
import time

import httpx
from dotenv import load_dotenv

load_dotenv()

url = "https://generativelanguage.googleapis.com/v1beta/models"
headers = {"x-goog-api-key": os.getenv("GOOGLE_API_KEY", "")}

start = time.time()
try:
    r = httpx.get(url, headers=headers, params={"pageSize": 1000}, timeout=20)
except httpx.TimeoutException as e:
    print("TIMED OUT after", round(time.time() - start, 1), "s:", type(e).__name__)
    raise SystemExit(1)

print("Status:", r.status_code, "in", round(time.time() - start, 1), "s")

if r.status_code == 200:
    wanted = os.getenv("MODEL_NAME", "")
    names = [
        m["name"].removeprefix("models/")
        for m in r.json().get("models", [])
        if "generateContent" in m.get("supportedGenerationMethods", [])
    ]
    print("Your MODEL_NAME is in the list:", wanted in names)
    print("Some available models:", names[:15])
else:
    print(r.text[:300])