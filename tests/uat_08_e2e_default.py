
import json
import os
from dotenv import load_dotenv
from src.processing.grouping.core import process_with_shrink
from src.llm.llm import LLMClient
from src.core.schemas import DocumentGroup

# Load environment variables for LLM API keys
load_dotenv()

class Page:
    """Mock Page class that mimics the attributes used by process_with_shrink."""
    def __init__(self, index, data):
        self.original_index = int(index)
        self.category = data.get("category", "unknown")
        self.canonical_tenant = data.get("expected_tenant_name", "Unknown Tenant")
        self.resolved_date = data.get("date", "Unknown Date")
        self.date = data.get("date", "Unknown Date")
        self.content_explanation = data.get("content_explanation", "")
        self.subject = data.get("subject", "")

def run_e2e_default_routing_test():
    print("🚀 Starting E2E Default Routing Test for Phase 08...")
    print("Scenario: Validating standard grouping for 'forms' category (Pages 194, 195, 196)\n")

    # 1. Load data from the report JSON
    json_path = "pdfs/1273/567_report.json"
    if not os.path.exists(json_path):
        print(f"❌ Error: Report file not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Extract a small group of forms
    target_pages = ["194", "195", "196"]
    pages = []
    for p_idx in target_pages:
        page_data = data.get(p_idx)
        if page_data:
            pages.append(Page(p_idx, page_data))
    
    print(f"📦 Loaded {len(pages)} form pages for testing.")
    for p in pages:
        print(f"  Page {p.original_index}: [forms] Content: {p.content_explanation[:60]}...")

    # 3. Initialize the real LLM Client
    try:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        llm_client = LLMClient(api_key=api_key)
        
        original_generate = llm_client.generate_content
        def wrapped_generate(contents, **kwargs):
            print("\n" + "!"*30)
            print("PROMPT SENT TO LLM:")
            print(contents[0] if isinstance(contents, list) else contents)
            print("!"*30 + "\n")
            return original_generate(contents, **kwargs)
        
        llm_client.generate_content = wrapped_generate
        print("\n✅ LLM Client initialized successfully.")
    except Exception as e:
        print(f"❌ Error initializing LLM Client: {e}")
        return

    # 4. Run the grouping logic
    print("\n🔍 Running process_with_shrink (Default Routing)...")
    try:
        groups = process_with_shrink(pages, llm_client)
    except Exception as e:
        print(f"❌ Error during grouping: {e}")
        return

    # 5. Display results
    print("\n" + "="*50)
    print("Grouping Results")
    print("="*50)
    
    for idx, group in enumerate(groups):
        print(f"Group {idx+1}: Pages {group.start_page} to {group.end_page}")
        print(f"  Category: {group.category}")
        print(f"  Reason:   {group.reason}")
        print("-" * 30)

    # 6. Validation check
    # Expectation: 194-195 together, 196 separate
    group_194_195 = any(g.start_page == 194 and g.end_page == 195 for g in groups)
    group_196 = any(g.start_page == 196 and g.end_page == 196 for g in groups)
    
    print("\n" + "="*50)
    if group_194_195 and group_196:
        print("🏆 RESULT: UAT-08.7 PASSED")
        print("The AI correctly grouped 194-195 and kept 196 separate.")
    else:
        print("❌ RESULT: UAT-08.7 FAILED")
        print(f"Expected groups [194-195] and [196]. Found: {len(groups)} groups.")
    print("="*50)

if __name__ == "__main__":
    run_e2e_default_routing_test()
