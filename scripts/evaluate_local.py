import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

# Add project root to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import Pipeline
from src.ingest import PdfIngestor
from src.llm import GemmaClient

def evaluate_local_models():
    load_dotenv()
    
    baseline_cache_path = "508.pdf.cache.json.bak"
    pdf_path = "508.pdf"
    
    if not os.path.exists(baseline_cache_path):
        print(f"Error: Baseline cache file '{baseline_cache_path}' not found.")
        return
        
    if not os.path.exists(pdf_path):
        print(f"Error: Target PDF file '{pdf_path}' not found.")
        return
        
    print(f"Loading baseline cloud results from '{baseline_cache_path}'...")
    with open(baseline_cache_path, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
        
    # We will only evaluate the pages present in our baseline cache
    pages_to_evaluate = sorted([int(k) for k in baseline_data.keys()])
    max_page = max(pages_to_evaluate)
    
    print(f"Initializing GemmaClient pointing to local models...")
    # Initialize client (keys are required but won't be used since we force local client calls)
    client = GemmaClient(api_keys=["dummy-eval-key"])
    ingestor = PdfIngestor()
    
    print(f"Extracting first {max_page} pages from '{pdf_path}'...")
    extracted_images = {}
    for page_idx, img_bytes in ingestor.extract_pages_as_images(pdf_path):
        if page_idx in pages_to_evaluate:
            extracted_images[page_idx] = img_bytes
        if page_idx >= max_page:
            break
            
    print(f"\nEvaluating local models on {len(pages_to_evaluate)} pages...")
    print(f"Local Vision OCR Model: {os.getenv('LOCAL_MODEL_NAME', 'qwen2.5vl:7b')}")
    print(f"Local Text Classify Model: {os.getenv('LOCAL_TEXT_MODEL_NAME', 'qwen2.5:14b')}")
    print(f"{'Page':<5} | {'Metric':<12} | {'Baseline (Cloud)':<30} | {'Local Model':<30} | {'Status'}")
    print("-" * 90)
    
    cat_matches = 0
    name_matches = 0
    total_duration = 0.0
    
    comparison_results = []
    
    for page_idx in pages_to_evaluate:
        img_bytes = extracted_images.get(page_idx)
        if not img_bytes:
            print(f"Page {page_idx} image missing from extraction.")
            continue
            
        baseline = baseline_data[str(page_idx)]
        
        start_time = time.time()
        try:
            # Force local two-step pipeline: Qwen-VL OCR -> Qwen-14B Classification
            # 1. Local OCR
            text = client._extract_text_with_qwen(img_bytes)
            # 2. Local Text Classification
            local_res = client._classify_text_with_local_model(text)
            duration = time.time() - start_time
            total_duration += duration
            
            baseline_cat = baseline.get("category", "")
            local_cat = local_res.category.value
            
            baseline_residents = sorted(baseline.get("residents", []))
            local_residents = sorted(local_res.residents)
            
            cat_match = (baseline_cat == local_cat)
            
            # Simple name set intersection check or semantic check
            # Convert to clean upper strings
            b_names_clean = {n.upper().strip() for n in baseline_residents if n not in ("NONE", "UNKNOWN", "")}
            l_names_clean = {n.upper().strip() for n in local_residents if n not in ("NONE", "UNKNOWN", "")}
            
            name_match = (b_names_clean == l_names_clean)
            
            if cat_match:
                cat_matches += 1
            if name_match:
                name_matches += 1
                
            status_cat = "✅ MATCH" if cat_match else "❌ MISMATCH"
            status_name = "✅ MATCH" if name_match else "❌ MISMATCH"
            
            print(f"{page_idx:<5} | {'Category':<12} | {baseline_cat:<30} | {local_cat:<30} | {status_cat} ({duration:.1f}s)")
            print(f"{'':<5} | {'Residents':<12} | {str(baseline_residents):<30} | {str(local_residents):<30} | {status_name}")
            print("-" * 90)
            
            comparison_results.append({
                "page": page_idx,
                "cat_match": cat_match,
                "name_match": name_match,
                "baseline_cat": baseline_cat,
                "local_cat": local_cat,
                "baseline_residents": baseline_residents,
                "local_residents": local_residents,
                "duration": duration
            })
            
        except Exception as e:
            print(f"{page_idx:<5} | Error running local pipeline on page {page_idx}: {e}")
            print("-" * 90)
            
    print("\n================== EVALUATION REPORT ==================")
    total_pages = len(pages_to_evaluate)
    cat_accuracy = (cat_matches / total_pages) * 100 if total_pages else 0
    name_accuracy = (name_matches / total_pages) * 100 if total_pages else 0
    avg_speed = total_duration / total_pages if total_pages else 0
    
    print(f"Total Evaluated Pages: {total_pages}")
    print(f"Category Classification Accuracy: {cat_accuracy:.1f}% ({cat_matches}/{total_pages})")
    print(f"Resident Name Extraction Accuracy: {name_accuracy:.1f}% ({name_matches}/{total_pages})")
    print(f"Average Processing Speed: {avg_speed:.2f}s per page (Total: {total_duration:.1f}s)")
    print("=======================================================")

if __name__ == "__main__":
    evaluate_local_models()
