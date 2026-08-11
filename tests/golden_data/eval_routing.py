import os
import json
import yaml
from pathlib import Path
from dotenv import dotenv_values
from src.llm.llm import LLMClient
from src.timeline.phase import load_and_parse_json
from src.pipeline.pipeline import Pipeline
from src.core.schemas import DocumentGroup
from src.categorization.fine_categorization import process_fine_categorization
from src.routing.config import FOLDER_PREFIXES

PREFIX_TO_FOLDER = {str(int(v)): k for k, v in FOLDER_PREFIXES.items()}

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
                
                cat_id = str(doc.get('category', ''))
                # Handle possible leading zeros or different formats
                try:
                    cat_id = str(int(cat_id))
                except ValueError:
                    pass
                    
                expected_folder = PREFIX_TO_FOLDER.get(cat_id, "Unknown")
                expected_routes[(start, end)] = expected_folder
                
                for p in pages:
                    truth_page_map[p - 1] = tenant_name
                    
    # 2. Load Raw Pages (Bypass Canonicalization Phase Completely)
    pages = load_and_parse_json(raw_dump_path)
    for page in pages:
        idx = getattr(page, 'original_index')
        page.canonical_tenant = truth_page_map.get(idx, "Unassigned")
        if not getattr(page, "resolved_date", None):
            page.resolved_date = getattr(page, "date", None)
            
    # 2.5 Run Fine Categorization
    print(f"Running fine categorization for {house_id}...")
    cache_path = Path(str(raw_dump_path) + '.fine_cache.json')
    
    cache_data = {}
    if cache_path.exists():
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
    missing_pages = []
    for idx, page in enumerate(pages):
        str_idx = str(idx)
        if str_idx in cache_data:
            page.fine_category = cache_data[str_idx].get('fine_category')
            page.fine_category_reason = cache_data[str_idx].get('fine_category_reason')
        else:
            missing_pages.append((idx, page))
            
    if missing_pages:
        missing_pages_only = [p for idx, p in missing_pages]
        processed_pages = process_fine_categorization(missing_pages_only, llm_client)
        
        for (idx, page), processed_page in zip(missing_pages, processed_pages):
            cache_data[str(idx)] = {
                'fine_category': getattr(processed_page, 'fine_category', None),
                'fine_category_reason': getattr(processed_page, 'fine_category_reason', None)
            }
            page.fine_category = getattr(processed_page, 'fine_category', None)
            page.fine_category_reason = getattr(processed_page, 'fine_category_reason', None)
            
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    # 3. Construct Perfect DocumentGroups (Bypass Grouping Phase Completely)
    perfect_groups = []
    for (start, end), expected_path in expected_routes.items():
        g_pages = pages[start:end+1]
        first_page = g_pages[0]
        category = getattr(first_page, "fine_category", getattr(first_page, "category", "UNKNOWN"))
        reason = getattr(first_page, "fine_category_reason", "Perfect Golden Grouping")
        title = getattr(first_page, "subject", getattr(first_page, "content_explanation", None))
        
        if any("صيانة" in getattr(p, "fine_category", "") for p in g_pages if getattr(p, "fine_category", "")):
            category = "10-صيانة"
            reason = "Deterministic Maintenance Set"
        elif any("عقود" in getattr(p, "fine_category", "") for p in g_pages if getattr(p, "fine_category", "")):
            category = "05-عقود"
            reason = "Deterministic Contract Set"
            
        primary_tenant = truth_page_map.get(start, "Unassigned")
        dates = [getattr(p, "resolved_date", None) for p in g_pages if getattr(p, "resolved_date", None)]
        
        doc_group = DocumentGroup(
            start_page=start,
            end_page=end,
            primary_tenant=primary_tenant,
            category=category,
            dates=dates,
            reason=reason,
            brief_arabic_title=title
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
        
    client = LLMClient(api_key=api_key, delay_between_pages=7.0)
    client.default_model = "gemma-4-31b-it"
    
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
