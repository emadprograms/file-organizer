import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest import PdfIngestor
from src.llm import GemmaClient
from src.schemas import PageClassification, Category

REPORT_PATH = SCRIPT_DIR / "local_vs_cloud_report.md"
PDF_PATH = PROJECT_ROOT / "508.pdf"

def get_page_image():
    if not PDF_PATH.exists():
        print(f"Error: '{PDF_PATH}' not found.")
        sys.exit(1)
        
    print(f"Extracting Page 52 from '{PDF_PATH}'...")
    ingestor = PdfIngestor()
    for page_idx, img_bytes in ingestor.extract_pages_as_images(str(PDF_PATH)):
        if page_idx == 52:
            return img_bytes
            
    print("Error: Could not extract page 52 from PDF.")
    sys.exit(1)

def run_comparison():
    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    img_bytes = get_page_image()
    
    # Use the qwen2.5vl:7b model for OCR
    os.environ["LOCAL_MODEL_NAME"] = "qwen2.5vl:7b"
    client = GemmaClient()
    
    ground_truth = {
        "category": Category.INSPECTION_PICTURES,
        "residents": ["NONE"],
        "date": "NONE",
        "is_continuation": False,
        "is_form": False
    }
    
    pipelines = {
        "Local Combo (qwen2.5vl + qwen2.5:14b)": "local"
    }
    
    iterations = 1
    results = {}
    
    for pipe_name, pipe_type in pipelines.items():
        print(f"\n==================================================")
        print(f"TESTING PIPELINE: {pipe_name} ({iterations} iterations)")
        print(f"==================================================")
        
        results[pipe_name] = []
        
        for i in range(1, iterations + 1):
            print(f"Run {i}/{iterations}...", end="", flush=True)
            start_time = time.time()
            
            run_data = {
                "run": i, "latency": 0.0, "success": False, "category_correct": False, "residents_correct": False
            }
            
            try:
                if pipe_type == "local":
                    # Local pipeline: vision OCR first, then local text classification
                    ocr_start = time.time()
                    text = client._extract_text_with_qwen(img_bytes)
                    ocr_time = time.time() - ocr_start
                    
                    print(f"\n[QWEN-VL OUTPUT]:\n{text}\n")
                    
                    reasoning_start = time.time()
                    parsed = client._classify_text_with_local_model(text)
                    reasoning_time = time.time() - reasoning_start
                    
                else:
                    # Cloud pipeline: direct multi-modal call
                    parsed = client.classify_page_direct(img_bytes)
                    
                duration = time.time() - start_time
                run_data["latency"] = duration
                
                if parsed:
                    run_data["success"] = True
                    run_data["category_correct"] = (parsed.category.value == ground_truth["category"].value)
                    
                    p_res = {n.strip() for n in parsed.residents if n not in ("NONE", "UNKNOWN", "")}
                    gt_res = {n.strip() for n in ground_truth["residents"]}
                    run_data["residents_correct"] = (p_res == gt_res)
                    
                    print(f" Done ({duration:.2f}s) | Category: {parsed.category.value} | Residents: {parsed.residents}")
                else:
                    print(f" Failed: parsed is None")
                    
            except Exception as e:
                duration = time.time() - start_time
                run_data["latency"] = duration
                print(f" Failed: {e}")
                
            results[pipe_name].append(run_data)
            time.sleep(2.0)  # Brief cooldown
            
    # Analyze and Output Report
    report_lines = []
    report_lines.append("# Local vs Cloud Pipeline Comparison\n")
    report_lines.append("| Pipeline | Success Rate | Avg Latency (s) | Min/Max Latency (s) | Category Match | Residents Match |")
    report_lines.append("|---|---|---|---|---|---|")
    
    summary_data = []
    
    for pipe_name in pipelines.keys():
        runs = results[pipe_name]
        successful_runs = [r for r in runs if r["success"]]
        num_success = len(successful_runs)
        
        if num_success > 0:
            avg_latency = sum(r["latency"] for r in successful_runs) / num_success
            min_latency = min(r["latency"] for r in successful_runs)
            max_latency = max(r["latency"] for r in successful_runs)
            
            cat_correct_pct = (sum(1 for r in successful_runs if r["category_correct"]) / num_success) * 100
            res_correct_pct = (sum(1 for r in successful_runs if r["residents_correct"]) / num_success) * 100
        else:
            avg_latency = min_latency = max_latency = cat_correct_pct = res_correct_pct = 0
            
        report_lines.append(
            f"| **{pipe_name}** | {num_success}/{iterations} | {avg_latency:.2f}s | {min_latency:.2f}s / {max_latency:.2f}s | {cat_correct_pct:.1f}% | {res_correct_pct:.1f}% |"
        )
        summary_data.append({"pipe": pipe_name, "success_rate": f"{num_success}/{iterations}", "avg_latency": f"{avg_latency:.2f}s", "accuracy": f"{cat_correct_pct:.0f}% Cat / {res_correct_pct:.0f}% Res"})
        
    report_text = "\n".join(report_lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)
        
    print("\n================== BENCHMARK SUMMARY ==================")
    for s in summary_data:
        print(f"{s['pipe']}:")
        print(f"  Success: {s['success_rate']} | Avg Time: {s['avg_latency']} | Accuracy: {s['accuracy']}")
    print("=========================================================")
    print(f"\nDetailed Markdown report saved to '{REPORT_PATH}'.")

if __name__ == "__main__":
    run_comparison()
