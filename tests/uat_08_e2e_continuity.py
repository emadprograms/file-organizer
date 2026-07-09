
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

def run_e2e_continuity_test():
    print("🚀 Starting E2E Continuity Test for Phase 08...")
    print("Scenario: Validating 'True Until Proven Guilty' logic on pages 1-10 of file 567\n")

    # 1. Load data from the fixture JSON
    json_path = "tests/fixtures/uat_08_continuity_data.json"
    if not os.path.exists(json_path):
        print(f"❌ Error: Fixture file not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Extract only the 'letters' from the fixture
    all_pages = []
    for i in range(1, 11):
        page_data = data.get(str(i))
        if page_data:
            all_pages.append(Page(i, page_data))
    
    pages = [p for p in all_pages if p.category == "letters"]
    
    print(f"📦 Loaded {len(pages)} letter pages for testing.")
    for p in pages:
        print(f"  Page {p.original_index}: [letters] Subject: {p.subject[:50]}...")

    # 3. Initialize the real LLM Client
    try:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        llm_client = LLMClient(api_key=api_key)
        
        # Intercept prompt to show the user exactly what is being sent
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
    print("\n🔍 Running process_with_shrink (this may take a few seconds)...")
    try:
        groups = process_with_shrink(pages, llm_client)
    except Exception as e:
        print(f"❌ Error during grouping: {e}")
        return

    # 5. Display results in a readable format
    print("\n" + "="*50)
    print("Grouping Results")
    print("="*50)
    
    for idx, group in enumerate(groups):
        print(f"Group {idx+1}: Pages {group.start_page} to {group.end_page}")
        print(f"  Category: {group.category}")
        print(f"  Tenant:   {group.primary_tenant}")
        print(f"  Reason:   {group.reason}")
        print("-" * 30)

    # 6. Validation check for UAT-08.3 and UAT-08.4
    # Target Story 1: Original indices 1, 2, 3 should be together.
    # Target Story 2: Original indices 4, 5, 6 should be together.
    # Hard Reset: Original index 8 should be separate.
    
    story1_passed = False
    story2_passed = False
    hard_reset_passed = True
    
    for group in groups:
        # Check for Story 1 (1-3)
        if group.start_page <= 1 and group.end_page >= 3:
            # Ensure it doesn't bleed into Story 2
            if group.end_page < 4:
                story1_passed = True
        
        # Check for Story 2 (4-6)
        if group.start_page <= 4 and group.end_page >= 6:
            # Ensure it doesn't bleed into Page 8
            if group.end_page < 8:
                story2_passed = True
            else:
                hard_reset_passed = False
    
    print("\n" + "="*50)
    if story1_passed and story2_passed and hard_reset_passed:
        print("🏆 RESULT: UAT-08.3 & UAT-08.4 PASSED")
        print("Story 1 (1-3) and Story 2 (4-6) are correctly isolated, and Page 8 is split.")
    else:
        print("❌ RESULT: FAILED")
        print(f"Story 1 (1-3) Passed: {story1_passed}")
        print(f"Story 2 (4-6) Passed: {story2_passed}")
        print(f"Hard Reset (8) Passed: {hard_reset_passed}")
    print("="*50)

if __name__ == "__main__":
    run_e2e_continuity_test()
