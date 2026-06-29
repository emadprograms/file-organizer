import fitz
import json
import os
import requests
import base64
import re
import time

CATEGORIES = [
    "contract", "forms", "id cards", "letters", 
    "others", "picture", "utility bill"
]

# You mentioned Qwen3.5 4B, but from your previous ollama list we saw:
# - qwen3-vl:latest
# - qwen3.5:9b
# Update this variable to exactly match the model tag you have in Ollama!
MODEL_NAME = "qwen3.5:4b" 

def classify_page(img_bytes, page_num):
    base64_image = base64.b64encode(img_bytes).decode('utf-8')
    
    prompt = (
        "You are a document classifier. Classify the document image into EXACTLY ONE "
        "of the following categories:\n"
        "- contract\n"
        "- forms\n"
        "- id cards\n"
        "- letters\n"
        "- others\n"
        "- picture\n"
        "- utility bill\n\n"
        "Because you are a reasoning model, you must think step-by-step first. "
        "Put your reasoning inside <think>...</think> tags. "
        "Once you are done thinking, you MUST output the final category on a new line in this EXACT format:\n"
        "FINAL_CATEGORY: <category_name>"
    )
    
    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [base64_image]
            }
        ],
        "stream": False,
        "options": {
            # Thinking models need more context tokens to hold their chain of thought!
            "num_ctx": 16384 
        }
    }
    
    response = requests.post("http://localhost:11434/api/chat", json=data)
    if response.status_code != 200:
        print(f"Ollama API Error: {response.status_code} {response.text}")
    response.raise_for_status()
    result = response.json()
    content = result.get('message', {}).get('content', '').strip()
    
    think_match = re.search(r"<think>(.*?)</think>", content, flags=re.DOTALL)
    if think_match:
        print(f"\n--- Model Thinking ---\n{think_match.group(1).strip()}\n----------------------")
    else:
        print(f"\n--- Model Thinking ---\n(No explicit <think> tags found, dumping content preview: {content[:200]}...)\n----------------------")
    
    # We parse the output to find "FINAL_CATEGORY: {category}" to avoid 
    # matching a category name that was just mentioned during the <think> phase.
    match = re.search(r"FINAL_CATEGORY:\s*([a-zA-Z\s]+)", content)
    if match:
        extracted_cat = match.group(1).strip().lower()
        for cat in CATEGORIES:
            if cat in extracted_cat:
                return cat
                
    # Fallback if the regex fails or format wasn't followed perfectly
    content_lower = content.lower()
    # Let's try to look at the very end of the output after the </think> tag
    if "</think>" in content_lower:
        after_think = content_lower.split("</think>")[-1]
        for cat in CATEGORIES:
            if cat in after_think:
                return cat
                
    print(f"[Warning] Unexpected output format for page {page_num}: {content}")
    return "others"

def main():
    pdf_path = "pdfs/1281_cleaned.pdf"
    output_path = f"scratch/1281_{MODEL_NAME.replace(':', '_')}_predictions.json"
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} does not exist.")
        return

    doc = fitz.open(pdf_path)
    predictions = {}
    
    total_pages = len(doc)
    print(f"Classifying {total_pages} pages from {pdf_path} using thinking model: {MODEL_NAME}...")
    
    # Keeping it at 3 pages for the initial test!
    for i in range(min(3, total_pages)):
        page = doc[i]
        pix = page.get_pixmap(dpi=50)
        img_bytes = pix.tobytes("png")
        
        print(f"Processing Page {i + 1}/{total_pages}...", flush=True)
        start_time = time.time()
        cat = classify_page(img_bytes, i + 1)
        end_time = time.time()
        elapsed = end_time - start_time
        
        predictions[str(i + 1)] = cat
        print(f"-> Result: {cat} (took {elapsed:.2f} seconds)", flush=True)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(predictions, f, indent=2)
            
    print(f"\nSaved predictions to {output_path}")

if __name__ == "__main__":
    main()
