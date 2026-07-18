from typing import Any
import pytest
from pydantic import ValidationError
from src.routing.router import route_document, RoutingResponse, RoutingValidationError
from src.core.schemas import DocumentGroup

class MockLLMClient:
    def __init__(self, responses) -> Any:
        """
        Provide the   init   fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self.responses = responses
        self.call_count = 0
        self.calls = []

    def generate_content(self, contents, response_schema=None, validation_context=None, **kwargs) -> Any:
        """
        Provide the generate content fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
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

def run_routing_scenario(responses, expected_folder=None, expect_error=False) -> Any:
    """
    Provide the run routing scenario fixture/mock.

    Returns:
    The appropriate fixture or mock value.
    """
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

def test_routing_hallucination_clean_route() -> None:
    """
    Test routing hallucination clean route.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    run_routing_scenario(["إشعارات"], expected_folder="إشعارات")

def test_routing_hallucination_recoverable() -> None:
    """
    Test routing hallucination recoverable.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    run_routing_scenario(["hallucinated_folder_123", "إشعارات"], expected_folder="إشعارات")

def test_routing_hallucination_terminal() -> None:
    """
    Test routing hallucination terminal.

    Expected outcome:
    The function should execute successfully and meet all assertions.
    """
    run_routing_scenario(["bad_1", "bad_2", "bad_3"], expect_error=True)
