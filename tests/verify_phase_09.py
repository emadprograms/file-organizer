import pytest
import sys

def main():
    print("=======================================")
    print("Phase 09 Verification Script")
    print("=======================================\n")

    tests = [
        ("Rate Limiting (429) Pauses and Retries", "tests/test_llm_resilience.py::test_resilience_429_retry_limit"),
        ("Server Error (500) Provider Rotation", "tests/test_llm_resilience.py::test_resilience_500_rotation"),
        ("Auth Error (401) Immediate Halt", "tests/test_llm_resilience.py::test_resilience_401_immediate_halt"),
        ("Secondary Provider Alternation", "tests/test_llm_resilience.py::test_provider_alternation"),
        ("Unmapped Category Raises Error (Hard Stop)", "tests/test_routing_safety.py::test_unmapped_category_raises_error"),
        ("LLM Exhaustion Raises Error", "tests/test_routing_safety.py::test_llm_exhaustion_raises_error"),
        ("Validation Failure Raises Error", "tests/test_routing_safety.py::test_validation_failure_raises_error"),
        ("Lockout Removal Verification", "tests/test_routing_safety.py::test_lockout_removal_verification")
    ]

    for desc, test_path in tests:
        print(f"\n--- Testing: {desc} ---")
        print(f"File: {test_path}")
        
        # Run pytest programmatically
        exit_code = pytest.main(["-v", "-s", test_path])
        
        if exit_code == 0:
            print("\n[PASS] Test passed successfully.")
        else:
            print(f"\n[FAIL] Test failed with exit code {exit_code}.")
            
        print("-" * 50)
        
        try:
            input("Press Enter to continue to the next test (or Ctrl+C to abort)... ")
        except KeyboardInterrupt:
            print("\nAborting verification.")
            sys.exit(0)

if __name__ == "__main__":
    main()
