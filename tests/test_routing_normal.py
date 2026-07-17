import pytest
from src.routing.router import route_document, RoutingValidationError
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
    llm = MockLLMClient([("إشعارات", "reason")])
    folder, direct = route_document(group, llm)
    assert folder == "إشعارات"
    assert direct is False
    print("UAT-09-01 PASS")

def test_uat_09_09_explicit_others():
    print("\nTesting UAT-09-09: Explicit 'others'")
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    llm = MockLLMClient([("رسائل متنوعة", "This clearly belongs in others")])
    folder, direct = route_document(group, llm)
    assert folder == "رسائل متنوعة"
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
