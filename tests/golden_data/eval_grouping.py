import os
import json
import yaml
from pathlib import Path
from dotenv import dotenv_values
from src.llm.llm import LLMClient
from src.timeline.phase import load_and_parse_json
from src.pipeline.pipeline import Pipeline

def evaluate_grouping(house_id: str, golden_yaml_path: Path, raw_dump_path: Path, llm_client: LLMClient) -> tuple[int, int]:
    # 1. Load Golden Truth Grouping
    with open(golden_yaml_path, 'r', encoding='utf-8') as f:
        golden_truth = yaml.safe_load(f)
        
    expected_groups = []
    truth_page_map = {}
    
    for tenant_name, t_data in golden_truth['tenants'].items():
        for doc in t_data['documents']:
            pages = doc['pages']
            if pages:
                start = min(pages) - 1
                end = max(pages) - 1
                expected_groups.append((start, end))
                for p in pages:
                    truth_page_map[p - 1] = tenant_name
                    
    # 2. Load Raw Pages (Bypass Canonicalization Phase Completely)
    pages = load_and_parse_json(raw_dump_path)
    
    # 3. Inject Perfect Golden Tenants to isolate grouping accuracy
    for page in pages:
        idx = getattr(page, 'original_index')
        page.canonical_tenant = truth_page_map.get(idx, "Unassigned")
        # Ensure resolved_date is somewhat populated for the fallback deterministic utility
        if not getattr(page, "resolved_date", None):
            page.resolved_date = getattr(page, "date", None)
            
    # 4. Run Grouping Phase
    pipeline = Pipeline(api_key=llm_client.api_key)
    pipeline.client = llm_client # Reuse client
    
    raw_pages = [(p.original_index, p) for p in pages]
    print(f"\n--- Grouping Evaluation for {house_id} ---")
    groups = pipeline._group_documents(raw_pages)
    
    actual_groups = [(g.start_page, g.end_page) for g in groups]
    
    correct = 0
    total = len(expected_groups)
    
    for expected in expected_groups:
        if expected in actual_groups:
            correct += 1
        else:
            print(f"\nMismatch: Expected document covering pages {expected[0]+1}-{expected[1]+1}")
            # Show what the expected pages were actually categorized as
            exp_pages = pages[expected[0]:expected[1]+1]
            print(f"   -> Expected Pages Category: {[getattr(p, 'category', 'N/A') for p in exp_pages]}")
            
            overlaps = [g for g in groups if max(expected[0], g.start_page) <= min(expected[1], g.end_page)]
            print(f"   -> Found overlapping output groups:")
            for og in overlaps:
                print(f"      * Pages {og.start_page+1}-{og.end_page+1} | Cat: {og.category} | Reason: {og.reason}")
            
    return correct, total

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        env = dotenv_values(".env")
        api_key = env.get("GEMINI_API_KEY")
        
    client = LLMClient(api_key=api_key, delay_between_pages=7.0)
    # Use standard flash-lite for grouping (much faster and more reliable than Gemma 4 for boundary JSON schema)
    client.default_model = "gemma-4-31b-it"
    
    target_dir = Path("tests/golden_data")
    houses = ["1155_R3322"]  # Run only one house at a time
    
    total_correct = 0
    total_pages = 0
    
    for house_id in houses:
        golden_yaml = target_dir / f"house_{house_id}_golden.yaml"
        raw_dump = target_dir / f"{house_id}.raw_dump.json"
        
        if not raw_dump.exists():
            raw_dump = target_dir / f"house_{house_id}_golden.raw_dump.json"
            
        if not raw_dump.exists():
            continue
            
        correct, total = evaluate_grouping(house_id, golden_yaml, raw_dump, client)
        print(f"Grouping Accuracy for {house_id}: {correct}/{total} ({(correct/total)*100 if total > 0 else 0:.2f}%)")
        
        total_correct += correct
        total_pages += total
        
    overall = (total_correct / total_pages) * 100 if total_pages > 0 else 0
    
    print(f"\n======================================")
    print(f"OVERALL GROUPING ACCURACY: {overall:.2f}%")
    print(f"======================================")
    
if __name__ == "__main__":
    main()
