import fitz
import json
import os
import time
from src.llm import LLMClient
from src.config import GEMINI_MODEL
from pydantic import BaseModel, Field
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class SimpleClassification(BaseModel):
    category: str = Field(description="Must be strictly one of: 'form', 'letter', or 'picture'")

def main():
    pdf_path = "pdfs/559.pdf"
    output_path = "scratch/ground_truth.json"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist.")
        return

    doc = fitz.open(pdf_path)
    client = LLMClient(api_key=os.getenv("GEMINI_API_KEY", ""))
    
    ground_truth = {}
    
    print(f"Classifying {len(doc)} pages from {pdf_path} using {GEMINI_MODEL}...")
    for i in range(min(5, len(doc))): # Process first 5 pages to build a small ground truth quickly
        page = doc[i]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        
        system_prompt = "You are a classifier. Classify the document image into EXACTLY ONE of these three categories: 'form', 'letter', or 'picture'. Return JSON matching the schema."
        user_prompt = "Classify this page."
        
        contents = [
            system_prompt,
            user_prompt,
            types.Part.from_bytes(data=img_bytes, mime_type='image/png')
        ]
        
        try:
            result = client._route_llm_call(
                model=GEMINI_MODEL,
                contents=contents,
                response_schema=SimpleClassification,
                log_prefix="GroundTruth"
            )
            cat = result.category.lower()
            if cat not in ['form', 'letter', 'picture']:
                cat = 'letter' # default fallback
                
            ground_truth[str(i + 1)] = cat
            print(f"Page {i + 1}: {cat}")
            
        except Exception as e:
            print(f"Error on page {i + 1}: {e}")
            ground_truth[str(i + 1)] = "letter"
            
        time.sleep(2) # rate limit prevention
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)
        
    print(f"Saved ground truth to {output_path}")

if __name__ == "__main__":
    main()
