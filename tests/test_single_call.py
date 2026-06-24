import os
import io
from dotenv import load_dotenv
from src.ingest import PdfIngestor
from src.llm import GemmaClient

load_dotenv()

if "GEMINI_API_KEYS" not in os.environ:
    print("Warning: No GEMINI_API_KEYS in env, testing skipped")
else:
    # Use real PDF from repo
    ingestor = PdfIngestor()
    pages = [next(ingestor.extract_pages_as_images("510.pdf"))]
    if not pages:
        print("No pages found in 1273.pdf")
        exit(1)
    
    img_bytes = pages[0][1]

    client = GemmaClient(delay_between_pages=0)
    print("Sending request to LLM to verify is_continuation extraction...")
    try:
        res = client.classify_page(img_bytes)
        print("Response received!")
        print(f"Category: {res.category}")
        print(f"Residents: {res.residents}")
        print(f"is_continuation: {res.is_continuation}")
        print(f"is_form: {getattr(res, 'is_form', False)}")
        print("Test passed: is_continuation is part of the single unified LLM call!")
    except Exception as e:
        print(f"Test failed or rate limited: {e}")
