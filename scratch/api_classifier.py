import sys
import fitz  # PyMuPDF
import requests

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(0)
    return page.get_text().strip()

def classify_hf_api(pdf_path):
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("No text found. Category: picture")
        return "picture"
        
    truncated_text = " ".join(text.split()[:400])
    
    # We use the Hugging Face free Serverless Inference API for zero-shot text classification
    # since local PyTorch DLLs are failing. This runs the exact same model.
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    
    payload = {
        "inputs": truncated_text,
        "parameters": {
            "candidate_labels": ["picture", "id", "form", "letter", "contract", "invoice", "bill"]
        }
    }
    
    print("Querying HuggingFace API for zero-shot classification...")
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        final_category = "others" if top_label in ["invoice", "bill"] else top_label
        
        print("\n--- Classification Result ---")
        print(f"File: {pdf_path}")
        print(f"Category: {final_category}")
        print(f"Raw Label: {top_label} (Confidence: {top_score:.2f})")
    else:
        print("API Error:", response.text)

if __name__ == "__main__":
    classify_hf_api(sys.argv[1])
