from typing import Any

import unittest
from unittest.mock import MagicMock
from src.grouping.core import process_with_shrink
from src.core.schemas import DocumentGroup

class MockPage:
    def __init__(self, index, category, tenant="Test Tenant", date="2020-01-16", content_explanation="Contract content", subject="Contract Subject") -> Any:
        """
        Provide the   init   fixture/mock.

        Returns:
        The appropriate fixture or mock value.
        """
        self.original_index = index
        self.category = category
        self.canonical_tenant = tenant
        self.resolved_date = date
        self.date = date
        self.content_explanation = content_explanation
        self.subject = subject

class TestUAT08Contracts(unittest.TestCase):
    def test_contract_grouping_deterministic(self) -> None:
        """
        Test contract grouping deterministic.

        Expected outcome:
        The function should execute successfully and meet all assertions.
        """
        # Data based on pages 9-15 of file 567
        pages = [
            MockPage(9, "05-عقود"),
            MockPage(10, "05-عقود"),
            MockPage(11, "05-عقود"),
            MockPage(12, "05-عقود"),
            MockPage(13, "05-عقود"),
            MockPage(14, "05-عقود"),
            MockPage(15, "05-عقود"),
        ]
        
        llm_client = MagicMock()
        groups = process_with_shrink(pages, llm_client)
        
        # Verify a single group was created
        self.assertEqual(len(groups), 1, "Should group all contract pages into one")
        self.assertEqual(groups[0].start_page, 9)
        self.assertEqual(groups[0].end_page, 15)
        self.assertEqual(groups[0].category, "05-عقود")
        
        # Verify LLM was bypassed
        llm_client.generate_content.assert_not_called()
        print("\nUAT-08.1 PASSED: Contracts grouped deterministically without LLM.")

if __name__ == "__main__":
    unittest.main()
