from google import genai
import os

from dotenv import load_dotenv
load_dotenv()

keys = os.environ.get("GEMINI_API_KEYS", "").split(",")
if not keys or not keys[0]:
    print("No keys found")
    exit(1)

client = genai.Client(api_key=keys[0])
for model in client.models.list():
    if "gemma" in model.name.lower():
        print(model.name)
