import os
import json
import yaml
from pathlib import Path
from dotenv import dotenv_values
from src.llm.llm import LLMClient
from src.timeline.phase import load_and_parse_json
from src.pipeline.pipeline import Pipeline
from src.core.schemas import DocumentGroup

def evaluate_routing(house_id: str, golden_yaml_path: Path, raw_dump_path: Path, llm_client: LLMClient) -> tuple[int, int]:
    # 1. Load Golden Truth Routing & Grouping
    with open(golden_yaml_path, 'r', encoding='utf-8') as f:
        golden_truth = yaml.safe_load(f)
        
    expected_routes = {}
    truth_page_map = {}
    
    for tenant_name, t_data in golden_truth['tenants'].items():
        for doc in t_data['documents']:
            pages = doc['pages']
            if pages:
                start = min(pages) - 1
                end = max(pages) - 1
                expected_routes[(start, end)] = doc['expected_path']
                for p in pages:
                    truth_page_map[p - 1] = tenant_name
                    
    # 2. Load Raw Pages (Bypass Canonicalization Phase Completely)
    pages = load_and_parse_json(raw_dump_path)
    for page in pages:
        idx = getattr(page, 'original_index')
        page.canonical_tenant = truth_page_map.get(idx, "Unassigned")
        if not getattr(page, "resolved_date", None):
            page.resolved_date = getattr(page, "date", None)
            
    # 3. Construct Perfect DocumentGroups (Bypass Grouping Phase Completely)
    perfect_groups = []
    for (start, end), expected_path in expected_routes.items():
        g_pages = pages[start:end+1]
        category = getattr(g_pages[0], "category", "UNKNOWN")
        primary_tenant = truth_page_map.get(start, "Unassigned")
        dates = [getattr(p, "resolved_date", None) for p in g_pages if getattr(p, "resolved_date", None)]
        
        doc_group = DocumentGroup(
            start_page=start,
            end_page=end,
            primary_tenant=primary_tenant,
            category=category,
            dates=dates,
            reason="Perfect Golden Grouping",
            brief_arabic_title=None
        )
        perfect_groups.append(doc_group)
        
    # 4. Run Routing Phase
    pipeline = Pipeline(api_key=llm_client.api_key)
    pipeline.client = llm_client
    
    print(f"\n--- Routing Evaluation for {house_id} ---")
    routed_groups = pipeline._route_documents(perfect_groups)
    
    correct = 0
    total = len(expected_routes)
    
    for doc in routed_groups:
        key = (doc.start_page, doc.end_page)
        expected = expected_routes.get(key)
        actual = getattr(doc, 'folder_path', '')
        
        # Windows/Linux path normalization for comparison
        expected_norm = expected.replace('\\', '/') if expected else ''
        actual_norm = actual.replace('\\', '/') if actual else ''
        
        # We might need to map exact paths depending on the golden data format
        if expected_norm == actual_norm:
            correct += 1
        else:
            print(f"Mismatch for pages {doc.start_page+1}-{doc.end_page+1}:")
            print(f"   -> Expected: {expected_norm}")
            print(f"   -> Output:   {actual_norm}")
            
    return correct, total

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        env = dotenv_values(".env")
        api_key = env.get("GEMINI_API_KEY")
        
    client = LLMClient(api_key=api_key, delay_between_pages=0.2)
    client.default_model = "gemini-3.5-flash"
    
    target_dir = Path("tests/golden_data")
    houses = ["1155_R3322", "1166_R3322", "1176_R3322", "1492_R3300"]
    
    total_correct = 0
    total_docs = 0
    
    for house_id in houses:
        golden_yaml = target_dir / f"house_{house_id}_golden.yaml"
        raw_dump = target_dir / f"{house_id}.raw_dump.json"
        
        if not raw_dump.exists():
            raw_dump = target_dir / f"house_{house_id}_golden.raw_dump.json"
            
        if not raw_dump.exists():
            continue
            
        correct, total = evaluate_routing(house_id, golden_yaml, raw_dump, client)
        print(f"Routing Accuracy for {house_id}: {correct}/{total} ({(correct/total)*100 if total > 0 else 0:.2f}%)")
        
        total_correct += correct
        total_docs += total
        
    overall = (total_correct / total_docs) * 100 if total_docs > 0 else 0
    
    print(f"\n======================================")
    print(f"OVERALL ROUTING ACCURACY: {overall:.2f}%")
    print(f"======================================")
    
if __name__ == "__main__":
    main()
