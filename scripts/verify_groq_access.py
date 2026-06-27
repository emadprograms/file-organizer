import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def verify_groq_access():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Error: GROQ_API_KEY not found in .env file.")
        return

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key,
    )

    models_to_test = [
        "llama-3.3-70b-versatile",
        "qwen/qwen3.6-27b"
    ]

    print(f"Testing Groq API access with key: {api_key[:8]}...{api_key[-4:]}")
    print("-" * 50)

    for model in models_to_test:
        print(f"Testing model: {model}...", end=" ", flush=True)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Access Verified'"}
                ],
                max_tokens=500
            )
            content = response.choices[0].message.content.strip()
            if "Access Verified" in content:
                print("✅ SUCCESS")
            else:
                print(f"⚠️ UNEXPECTED RESPONSE:\n{'-' * 20}\n{content}\n{'-' * 20}")
        except Exception as e:
            print(f"❌ FAILED: {e}")

    print("-" * 50)
    print("Verification complete.")

if __name__ == "__main__":
    verify_groq_access()
