import os
os.environ["GEMINI_API_KEY"] = "invalid_gemini_key"
os.environ["OPENROUTER_API_KEY"] = "invalid_openrouter_key"
os.environ["GROQ_API_KEY"] = "invalid_groq_key"

from src.llm import GemmaClient
from pydantic import BaseModel

class DummyResponse(BaseModel):
    dummy: str

client = GemmaClient(api_key="invalid_gemini_key")
try:
    client._route_llm_call(model="gemini-1.5-flash", contents=["hello"], response_schema=DummyResponse)
except Exception as e:
    import traceback
    traceback.print_exc()
