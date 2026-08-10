import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.categorization.fine_categorization import process_fine_categorization

class MockPage:
    def __init__(self, content_explanation, category="letters", subject=""):
        self.content_explanation = content_explanation
        self.category = category
        self.subject = subject

def test_fine_categorization():
    print("Running fine categorization test...")
    pages = [
        MockPage("Fixing the broken window in the living room", "letters", "Maintenance Request"),
        MockPage("Monthly rent payment receipt", "letters", "Rent Receipt")
    ]
    
    mock_llm = MagicMock()
    mock_llm.generate_content.side_effect = [
        MagicMock(reason="This is about fixing a window", category="10-صيانة"),
        MagicMock(reason="This is about rent deduction", category="07-استقطاع إيجار")
    ]
    
    result = process_fine_categorization(pages, mock_llm)
    
    assert result[0].fine_category == "10-صيانة"
    assert result[1].fine_category == "07-استقطاع إيجار"
    print("Test passed successfully!")

if __name__ == "__main__":
    test_fine_categorization()
