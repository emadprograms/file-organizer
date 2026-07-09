
import unittest
from unittest.mock import MagicMock, patch
from src.processing.grouping.core import process_with_shrink
from src.processing.grouping.config import LETTER_PROMPT, FORM_PROMPT, OTHER_PROMPT
from src.core.schemas import DocumentGroup

class MockPage:
    def __init__(self, index, category, tenant="Test Tenant", date="2023-01-01", content_explanation="Some content", subject="Some subject"):
        self.original_index = index
        self.category = category
        self.canonical_tenant = tenant
        self.resolved_date = date
        self.date = date
        self.content_explanation = content_explanation
        self.subject = subject

class TestPhase08Grouping(unittest.TestCase):
    def test_config_prompts(self):
        self.assertIn("True Until Proven Guilty", LETTER_PROMPT)
        self.assertIn("Hard Reset", LETTER_PROMPT)
        self.assertIn("tables", LETTER_PROMPT)

    def test_deterministic_bypass_contracts(self):
        pages = [
            MockPage(10, "contract"),
            MockPage(11, "contract"),
            MockPage(12, "contract")
        ]
        llm_client = MagicMock()
        groups = process_with_shrink(pages, llm_client)
        
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].start_page, 10)
        self.assertEqual(groups[0].end_page, 12)
        self.assertEqual(groups[0].category, "contract")
        llm_client.generate_content.assert_not_called()

    def test_deterministic_bypass_utility_bills(self):
        pages = [
            MockPage(20, "utility_bills"),
            MockPage(21, "utility_bills")
        ]
        llm_client = MagicMock()
        groups = process_with_shrink(pages, llm_client)
        
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0].start_page, 20)
        self.assertEqual(groups[0].end_page, 20)
        self.assertEqual(groups[1].start_page, 21)
        self.assertEqual(groups[1].end_page, 21)
        llm_client.generate_content.assert_not_called()

    @patch('src.processing.grouping.core._process_chunk')
    def test_dynamic_routing_others(self, mock_process_chunk):
        # Mock _process_chunk to return a group
        mock_process_chunk.return_value = [
            DocumentGroup(start_page=0, end_page=1, primary_tenant="T", category="others", dates=[], reason="R")
        ]
        
        pages = [
            MockPage(0, "others"),
            MockPage(1, "others"),
            MockPage(2, "others")
        ]
        llm_client = MagicMock()
        process_with_shrink(pages, llm_client)
        
        # For "others", CHUNK_SIZES = [2]
        # First call should be current_page_index=0, end_index=2
        mock_process_chunk.assert_any_call(pages, 0, 2, llm_client, OTHER_PROMPT, "content_explanation")

    @patch('src.processing.grouping.core._process_chunk')
    def test_dynamic_routing_letters(self, mock_process_chunk):
        mock_process_chunk.return_value = [
            DocumentGroup(start_page=0, end_page=0, primary_tenant="T", category="letters", dates=[], reason="R")
        ]
        
        pages = [
            MockPage(0, "letters"),
            MockPage(1, "letters")
        ]
        llm_client = MagicMock()
        process_with_shrink(pages, llm_client)
        
        # For "letters", prompt=LETTER_PROMPT, content_field="subject"
        mock_process_chunk.assert_any_call(pages, 0, 10 if len(pages) > 10 else len(pages), llm_client, LETTER_PROMPT, "subject")

if __name__ == "__main__":
    unittest.main()
