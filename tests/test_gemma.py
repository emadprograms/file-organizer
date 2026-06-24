import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.llm import GemmaClient
from src.ingest import PdfIngestor
from src.schemas import PageClassification

load_dotenv()

def test():
    keys = os.environ.get("GEMINI_API_KEYS", "").split(",")
    key = keys[0]
    client = genai.Client(api_key=key)
    
    ingestor = PdfIngestor()
    pages = list(ingestor.extract_pages_as_images("sample.pdf"))
    first_page_bytes = pages[0][1]

    llm = GemmaClient(api_keys=[key])
    system_prompt = llm._build_system_prompt()
    user_prompt = "Classify this scanned document page."

    print("Testing 3 parts + schema + NEW prompt...")
    try:
        response = client.models.generate_content(
            model='gemma-4-31b-it',
            contents=[
                system_prompt,
                user_prompt,
                types.Part.from_bytes(data=first_page_bytes, mime_type='image/png')
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PageClassification,
                temperature=0
            )
        )
        print("Success!")
    except Exception as e:
        print("Failed:", repr(e))

    print("Testing combined string + schema + NEW prompt...")
    try:
        combined = system_prompt + "\n\n" + user_prompt
        response = client.models.generate_content(
            model='gemma-4-31b-it',
            contents=[
                combined,
                types.Part.from_bytes(data=first_page_bytes, mime_type='image/png')
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PageClassification,
                temperature=0
            )
        )
        print("Success!")
    except Exception as e:
        print("Failed:", repr(e))

if __name__ == "__main__":
    test()
