import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm import GemmaClient
from src.schemas import PageClassification, Category

CACHE_PATH = SCRIPT_DIR / "page_2_ocr_cache.json"

def get_ocr_text():
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)["text"]
    print(f"Error: Cache not found at {CACHE_PATH}")
    sys.exit(1)

def run_stress_test():
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    ocr_text = get_ocr_text()
    
    client = GemmaClient(api_keys=["dummy"])
    system_prompt = client._build_system_prompt()
    user_prompt = f"Classify this scanned document page based on the following extracted text.\n\nExtracted Text:\n{ocr_text}"
    
    ground_truth = {
        "category": Category.AMAR_TAKHSEES,
        "residents": ["عبدالله عيسى الكواري"],
        "date": "2023-05-16",
        "is_continuation": False,
        "is_form": False
    }
    
    models = ["qwen3.5:9b"]
    iterations = 5
    
    results = {}
    
    for model in models:
        print(f"\n==================================================")
        print(f"STRESS TESTING MODEL: {model} ({iterations} iterations)")
        print(f"==================================================")
        
        results[model] = []
        
        for i in range(1, iterations + 1):
            print(f"Run {i}/{iterations}...", end="", flush=True)
            start_time = time.time()
            
            run_data = {
                "run": i, "latency": 0.0, "parsed_success": False
            }
            
            try:
                response = client.local_client.beta.chat.completions.parse(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=PageClassification,
                    temperature=0.0,
                    extra_body={"options": {"num_ctx": 8192}}
                )
                
                duration = time.time() - start_time
                run_data["latency"] = duration
                
                if response.choices[0].message.parsed:
                    parsed = response.choices[0].message.parsed
                    run_data["parsed_success"] = True
                    print(f" Done ({duration:.2f}s) | Category: {parsed.category.value} | Residents: {parsed.residents}")
                else:
                    print(f" Failed: parsed is None")
                    
            except Exception as e:
                duration = time.time() - start_time
                run_data["latency"] = duration
                print(f" Failed: {e}")
                
            results[model].append(run_data)
            time.sleep(1.0)
            
    print("\n================== STRESS TEST SUMMARY ==================")
    for model in models:
        runs = results[model]
        successful_runs = [r for r in runs if r["parsed_success"]]
        num_success = len(successful_runs)
        if num_success > 0:
            avg_latency = sum(r["latency"] for r in successful_runs) / num_success
            print(f"Model: {model}")
            print(f"  Success Rate: {num_success}/{iterations}")
            print(f"  Average Latency: {avg_latency:.2f}s")
        else:
            print(f"Model: {model} completely failed.")
    print("=========================================================")

if __name__ == "__main__":
    run_stress_test()
