import logging
import sys
from pydantic import ValidationError
from src.processing.routing.router import route_document, RoutingResponse, RoutingValidationError
from src.core.schemas import DocumentGroup

# Setup logging to see the retry feedback in the console
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("uat")

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

def run_scenario(name, responses, expected_folder=None, expect_error=False):
    print(f"\n--- Running Scenario: {name} ---")
    group = DocumentGroup(
        start_page=0, end_page=1, primary_tenant="Test",
        category="letters", dates=["2023-01-01"]
    )
    llm = MockLLMClient(responses)
    
    try:
        folder, direct = route_document(group, llm)
        print(f"Result: Success! Routed to '{folder}'")
        print(f"LLM Calls: {llm.call_count}")
        
        if expected_folder and folder != expected_folder:
            print(f"❌ FAILED: Expected {expected_folder}, got {folder}")
            return False
        
        if expect_error:
            print("❌ FAILED: Expected RoutingValidationError but succeeded")
            return False
            
        print("✅ PASSED")
        return True
        
    except RoutingValidationError as e:
        print(f"Result: Caught expected RoutingValidationError: {e}")
        print(f"LLM Calls: {llm.call_count}")
        if expect_error:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED: Unexpected RoutingValidationError")
            return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected exception: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    # Valid folder for 'letters' category (from config)
    VALID_FOLDER = "8_complaints_and_violations"
    
    scenarios = [
        {
            "name": "Scenario 1: Clean Route",
            "responses": [VALID_FOLDER],
            "expected_folder": VALID_FOLDER,
            "expect_error": False
        },
        {
            "name": "Scenario 2: Recoverable Hallucination",
            "responses": ["hallucinated_folder_123", VALID_FOLDER],
            "expected_folder": VALID_FOLDER,
            "expect_error": False
        },
        {
            "name": "Scenario 3: Terminal Hallucination",
            "responses": ["bad_1", "bad_2", "bad_3"],
            "expected_folder": None,
            "expect_error": True
        }
    ]

    all_passed = True
    for s in scenarios:
        if not run_scenario(s["name"], s["responses"], s["expected_folder"], s["expect_error"]):
            all_passed = False

    print("\n" + "="*30)
    if all_passed:
        print("OVERALL UAT RESULT: PASS")
        sys.exit(0)
    else:
        print("OVERALL UAT RESULT: FAIL")
        sys.exit(1)
