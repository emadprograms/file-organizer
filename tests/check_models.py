import os
from dotenv import load_dotenv
from google import genai

def test_models():
    load_dotenv(dotenv_path=".env")
    api_keys_str = os.getenv("GEMINI_API_KEYS")
    if not api_keys_str:
        print("No keys found")
        return
    
    first_key = api_keys_str.split(",")[0].strip()
    client = genai.Client(api_key=first_key)
    
    models_to_test = [
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-3.0-flash",
        "gemini-3.5-flash",
        "gemma-2-27b-it"
    ]
    
    print("Testing Models on Google API...")
    for m in models_to_test:
        try:
            response = client.models.generate_content(
                model=m,
                contents="Reply with the word OK."
            )
            print(f"[SUCCESS] {m} works! Reply: {response.text.strip()}")
        except Exception as e:
            error_str = str(e).replace('\n', ' ')
            print(f"[FAILED] {m} -> {error_str[:100]}...")

if __name__ == "__main__":
    test_models()
