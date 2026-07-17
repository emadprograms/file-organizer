import pytest
from pydantic import ValidationError
from src.routing.router import route_document, RoutingResponse, RoutingValidationError
from src.core.schemas import DocumentGroup

class MockLLMClient:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
        self.calls = []

    def generate_content(self, contents, response_schema=None, validation_context=None, **kwargs):
        self.calls.append(contents)
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            if response_schema:
                # Simulate Pydantic's model_validate with context
                data = {"selected_folder": resp, "reason": "Mock reason for UAT"}
                return response_schema.model_validate(data, context=validation_context)
            return resp
        raise Exception("No more mock responses")

def run_routing_scenario(responses, expected_folder=None, expect_error=False):
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    llm = MockLLMClient(responses)
    
    try:
        folder, direct = route_document(group, llm)
        if expect_error:
            pytest.fail("Expected RoutingValidationError but succeeded")
        if expected_folder:
            assert folder == expected_folder, f"Expected {expected_folder}, got {folder}"
    except RoutingValidationError as e:
        if not expect_error:
            pytest.fail(f"Unexpected RoutingValidationError: {e}")

def test_routing_hallucination_clean_route():
    run_routing_scenario(["8_complaints_and_violations"], expected_folder="8_complaints_and_violations")

def test_routing_hallucination_recoverable():
    run_routing_scenario(["hallucinated_folder_123", "8_complaints_and_violations"], expected_folder="8_complaints_and_violations")

def test_routing_hallucination_terminal():
    run_routing_scenario(["bad_1", "bad_2", "bad_3"], expect_error=True)
