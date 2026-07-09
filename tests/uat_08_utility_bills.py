
import unittest
from unittest.mock import MagicMock
from src.processing.grouping.core import process_with_shrink
from src.core.schemas import DocumentGroup

class MockPage:
    def __init__(self, index, category, tenant="Test Tenant", date="2017-10-15", content_explanation="Utility bill content", subject="Bill Subject"):
        self.original_index = index
        self.category = category
        self.canonical_tenant = tenant
        self.resolved_date = date
        self.date = date
        self.content_explanation = content_explanation
        self.subject = subject

class TestUAT08UtilityBills(unittest.TestCase):
    def test_utility_bill_splitting_deterministic(self):
        # Data based on extracted utility bills from file 567 (pages 99, 123, 138, 145)
        pages = [
            MockPage(99, "utility_bills"),
            MockPage(123, "utility_bills"),
            MockPage(138, "utility_bills"),
            MockPage(145, "utility_bills"),
        ]
        
        llm_client = MagicMock()
        groups = process_with_shrink(pages, llm_client)
        
        # Verify that each page is split into its own DocumentGroup
        self.assertEqual(len(groups), 4, "Each utility bill should be a separate document")
        
        # Verify indices are correct
        self.assertEqual(groups[0].start_page, 99)
        self.assertEqual(groups[0].end_page, 99)
        self.assertEqual(groups[3].start_page, 145)
        self.assertEqual(groups[3].end_page, 145)
        
        # Verify LLM was bypassed
        llm_client.generate_content.assert_not_called()
        print("\nUAT-08.2 PASSED: Utility bills split deterministically without LLM.")

if __name__ == "__main__":
    unittest.main()
