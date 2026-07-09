import pytest
from src.processing.routing.router import route_document, RoutingValidationError
from src.core.schemas import DocumentGroup
from unittest.mock import MagicMock

class MockLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        
    def generate_content(self, contents, model=None, response_schema=None, config=None, **kwargs):
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            if isinstance(resp, tuple):
                data = {"selected_folder": resp[0], "reason": resp[1]}
            else:
                data = {"selected_folder": resp, "reason": "mock reason"}
            return response_schema.model_validate(data, context=kwargs.get('validation_context', {}))
        raise Exception("No more mock responses")

def test_uat_09_01_normal_routing():
    print("\nTesting UAT-09-01: Normal Routing")
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    llm = MockLLMClient([("8_complaints_and_violations", "reason")])
    folder, direct = route_document(group, llm)
    assert folder == "8_complaints_and_violations"
    assert direct is False
    print("UAT-09-01 PASS")

def test_uat_09_09_explicit_others():
    print("\nTesting UAT-09-09: Explicit '13_others'")
    # Ensure 'letters' allows '13_others'
    from src.processing.routing.config import CATEGORY_TO_FOLDERS
    if "13_others" not in CATEGORY_TO_FOLDERS.get("letters", []):
        CATEGORY_TO_FOLDERS["letters"].append("13_others")
    
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    llm = MockLLMClient([("13_others", "This clearly belongs in others")])
    folder, direct = route_document(group, llm)
    assert folder == "13_others"
    assert direct is False
    print("UAT-09-09 PASS")

if __name__ == "__main__":
    try:
        test_uat_09_01_normal_routing()
        test_uat_09_09_explicit_others()
        print("\nALL UAT VERIFICATIONS PASSED")
    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        exit(1)
