import os
from src.llm import GemmaClient
from pydantic import BaseModel

class Dummy(BaseModel):
    test: str

def main():
    os.environ["GEMINI_API_KEY"] = "invalid_gemini"
    os.environ["OPENROUTER_API_KEY"] = "invalid_openrouter"
    os.environ["GROQ_API_KEY"] = "invalid_groq"
    
    client = GemmaClient(api_key="invalid_gemini")
    print(client.api_key)
    try:
        client._route_llm_call("gemini-2.5-flash", ["hello"], Dummy)
    except Exception as e:
        print(f"FAILED WITH: {type(e)}: {e}")

if __name__ == "__main__":
    main()
