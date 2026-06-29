import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load API keys from the project .env file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

def main():
    print("Loading image...")
    # Dynamically resolve the path so it works regardless of where you run the script from
    image_path = os.path.join(os.path.dirname(__file__), 'page-15_cleaned.png')
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        
    part = types.Part.from_bytes(data=image_bytes, mime_type='image/png')
    
    # In src/config.py and src/llm.py, 'gemma-4-31b-it' is accessed via the GEMINI API
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = "Please read this scanned Arabic document and provide its full contents perfectly translated into English."
    
    print("Sending to gemma-4-26b-a4b-it...")
    try:
        response = client.models.generate_content(
            model='gemma-4-26b-a4b-it',
            contents=[prompt, part]
        )
        print("Saving translation to translation_output.txt...")
        with open(os.path.join(os.path.dirname(__file__), 'translation_output.txt'), 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
