import os
from google import genai
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = "Hello, are you there?"

    print("Sending text prompt to gemma-4-26b-a4b-it...")
    try:
        response = client.models.generate_content(
            model='gemma-4-26b-a4b-it',
            contents=[prompt]
        )
        print("--- Output ---")
        print(response.text)
        print("--------------------------")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
