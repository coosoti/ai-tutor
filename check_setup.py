import os
import sys
from importlib.metadata import version

from dotenv import load_dotenv

load_dotenv()

print("Python:", sys.version.split()[0])
for pkg in ["langchain", "langgraph", "langchain-google-genai"]:
    print(pkg, version(pkg))

key = os.getenv("GOOGLE_API_KEY")
print("API key found:", bool(key))
print("Model name:", os.getenv("MODEL_NAME"))