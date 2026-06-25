import os
import sys

# Add project root to sys.path so we can import src modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.llm import GemmaClient

def run_tests():
    print("Initializing GemmaClient...")
    # Provide a dummy API key just to pass the init check in case env var is missing
    client = GemmaClient(api_keys=["dummy_test_key"])
    
    test_cases = [
        # Match expected
        ("محمد علي أحمد", "المحمد علي احمد", True, "Arabic prefix 'Al-' and missing Hamza"),
        ("السيد خالد عبدالله", "خالد عبدالله", True, "Arabic title 'السيد' (Mr.) vs None"),
        ("آمنة يوسف (زوجة)", "آمنة يوسف", True, "Relationship appended vs plain name"),
        ("عبدالرحمن بن سعود", "عبد الرحمن سعود", True, "Spacing in Abdul and 'بن' (bin)"),
        ("فاطمة الزهراء علي", "فاطمة علي", True, "Missing middle name"),
        ("المرحوم عبدالله سعيد", "عبدالله سعيد", True, "Title 'المرحوم' (The late) vs None"),
        ("ورثة أحمد خليل", "أحمد خليل", True, "Prefix 'ورثة' (Heirs of) vs None"),
        ("Robert Downey Jr.", "Robert Downey", True, "English suffix"),
        ("Mohamed Hussain", "Muhammad Hossein", True, "English spelling variations of Arabic names"),
        
        # Non-match expected
        ("محمد علي", "يوسف علي", False, "Different first names but same last name"),
        ("Jane Doe", "John Doe", False, "Different English first names")
    ]
    
    print(f"\nRunning {len(test_cases)} test cases against the local LLM name matcher...\n" + "="*80)
    
    passed = 0
    for name1, name2, expected_match, description in test_cases:
        print(f"Test: {description}")
        print(f"Names: '{name1}' vs '{name2}'")
        print(f"Expected: {expected_match}")
        
        try:
            # We use 'contract' as a generic category context
            result = client.check_name_match(name1, name2, "contract")
            
            # Print the LLM's reason from the cache indirectly, but wait!
            # check_name_match just returns the boolean. 
            # The reason is parsed inside but not returned.
            # To see the reason, we might need to modify check_name_match or just trust the boolean.
            print(f"LLM Result: {result}")
            
            if result == expected_match:
                print("✅ PASSED\n" + "-"*80)
                passed += 1
            else:
                print("❌ FAILED\n" + "-"*80)
                
        except Exception as e:
            print(f"⚠️ ERROR: {e}\n" + "-"*80)
            
    print(f"\nTests Completed: {passed}/{len(test_cases)} Passed.")

if __name__ == "__main__":
    run_tests()
