import unittest
from unittest.mock import patch, MagicMock
import time
import os
import json

from src.llm import GemmaClient, InvalidResponseError, LLMFailureError
from src.pipeline import Pipeline
from src.schemas import Category

class TestLLMResilience(unittest.TestCase):
    def setUp(self):
        # Reset state
        GemmaClient.global_rpm_tracker.clear()
        GemmaClient.global_cooldown_until = 0.0

    @patch('src.llm.time.sleep')
    @patch('src.llm.time.time')
    @patch('src.llm.genai.Client')
    def test_invalid_response_raises_after_2_retries(self, MockGenaiClient, MockTime, MockSleep):
        mock_genai = MagicMock()
        MockGenaiClient.return_value = mock_genai
        client = GemmaClient(api_keys=["test-key"])
        
        mock_response = MagicMock()
        mock_response.parsed = None
        mock_response.usage_metadata = None
        mock_response.text = "```html\n<not json>\n```"
        mock_genai.models.generate_content.return_value = mock_response

        current_time = [1000000.0]
        def mock_time(): return current_time[0]
        def mock_sleep(secs): current_time[0] += secs
        MockTime.side_effect = mock_time
        MockSleep.side_effect = mock_sleep
        
        with self.assertRaises(InvalidResponseError):
            client.classify_page(b"fake_bytes")
            
        self.assertEqual(mock_genai.models.generate_content.call_count, 2)

    @patch('src.llm.time.sleep')
    @patch('src.llm.time.time')
    @patch('src.llm.genai.Client')
    def test_global_cooldown_on_429(self, MockGenaiClient, MockTime, MockSleep):
        mock_genai = MagicMock()
        MockGenaiClient.return_value = mock_genai
        client = GemmaClient(api_keys=["test-key"])
        
        mock_genai.models.generate_content.side_effect = Exception("429 Resource Exhausted")
        
        current_time = [1000000.0]
        def mock_time(): return current_time[0]
        def mock_sleep(secs): current_time[0] += secs
        MockTime.side_effect = mock_time
        MockSleep.side_effect = mock_sleep
        
        now = current_time[0]
        
        with self.assertRaises((LLMFailureError, RuntimeError)):
            client.classify_page(b"fake_bytes")
            
        self.assertGreaterEqual(GemmaClient.global_cooldown_until, now + 65.0)

    @patch('src.pipeline.PdfIngestor')
    def test_pipeline_fallback(self, MockIngestor):
        pipeline = Pipeline(api_keys=["test-key"])
        
        mock_ingestor_instance = MockIngestor.return_value
        mock_ingestor_instance.extract_pages_as_images.return_value = [(1, b"0" * 16000)]
        pipeline.ingestor = mock_ingestor_instance
        
        pipeline.client = MagicMock()
        pipeline.client.classify_page.side_effect = InvalidResponseError("Bad JSON")
        
        with patch('os.path.exists', return_value=False), \
             patch('builtins.open', unittest.mock.mock_open()), \
             patch('os.replace'):
            
            groups = pipeline.process_pdf("dummy.pdf")
            
            self.assertEqual(len(groups), 1)
            self.assertEqual(groups[0].category, Category.OTHER_LETTERS)
            self.assertEqual(groups[0].primary_tenant, "UNKNOWN")

if __name__ == '__main__':
    unittest.main()
