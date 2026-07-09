
import unittest
from unittest.mock import MagicMock, patch
from src.processing.grouping.core import process_with_shrink
from src.core.schemas import DocumentGroup

class MockPage:
    def __init__(self, index, category="others"):
        self.original_index = index
        self.category = category
        self.canonical_tenant = "Test Tenant"
        self.resolved_date = "2023-01-01"
        self.date = "2023-01-01"
        self.content_explanation = "Some other content"
        self.subject = "Some other subject"

class TestUAT08PrecisionWindow(unittest.TestCase):
    @patch('src.processing.grouping.core._process_chunk')
    def test_others_precision_window(self, mock_process_chunk):
        # Mock _process_chunk to return a valid group so it doesn't fail validation
        mock_process_chunk.return_value = [
            DocumentGroup(start_page=0, end_page=1, primary_tenant="T", category="others", dates=[], reason="R")
        ]
        
        # Pages 30-33 are all "others"
        pages = [
            MockPage(30, "others"),
            MockPage(31, "others"),
            MockPage(32, "others"),
            MockPage(33, "others"),
        ]
        
        llm_client = MagicMock()
        process_with_shrink(pages, llm_client)
        
        # For category "others", CHUNK_SIZES should be [2].
        # The while loop in process_with_shrink should call _process_chunk with:
        # current_page_index=0, end_index=2
        # Then current_page_index=1, end_index=3 (due to overlap=1)
        # Then current_page_index=2, end_index=4
        
        # We check if any call was made with a chunk size larger than 2
        for call in mock_process_chunk.call_args_list:
            args, kwargs = call
            current_idx = args[1]
            end_idx = args[2]
            chunk_size = end_idx - current_idx
            self.assertLessEqual(chunk_size, 2, f"Chunk size {chunk_size} exceeds precision window of 2 for 'others'")

        print("\nUAT-08.6 PASSED: Precision window of 2 enforced for 'others' category.")

if __name__ == "__main__":
    unittest.main()
