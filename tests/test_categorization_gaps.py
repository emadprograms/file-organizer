import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.categorization.categorization import process_unclassified_pdf
from src.llm.llm import LLMClient
from src.core.schemas import CategorizationResult

class MockBypassLLM(LLMClient):
    def __init__(self):
        self.call_count = 0
        
    @property
    def provider(self):
        return MagicMock()

    def upload_file(self, file_path):
        return MagicMock(name="uploaded_file")
        
    def delete_file(self, file_obj):
        pass

    def generate_content(self, contents, response_schema=None, **kwargs):
        self.call_count += 1
        return MagicMock()

@patch("src.categorization.categorization.process_pdf")
def test_bypass_if_report_exists(mock_process_pdf, tmp_path):
    """
    Test CAT-02: System can bypass the LLM/OCR extraction step entirely 
    if a _report.json file is already present for the document.
    """
    # Setup mock PDF
    test_pdf = tmp_path / "doc1.pdf"
    test_pdf.touch()
    
    # Create the bypass file
    report_file = tmp_path / "doc1_report.json"
    report_file.write_text("[]")
    
    llm_client = MockBypassLLM()
    
    process_unclassified_pdf(tmp_path, llm_client)
    
    # Process PDF should not be called
    mock_process_pdf.assert_not_called()
    
    # LLM should not be called
    assert llm_client.call_count == 0

@patch("src.categorization.categorization.process_pdf")
def test_bypass_if_global_report_exists(mock_process_pdf, tmp_path):
    """
    Test CAT-02 with _report.json.
    """
    test_pdf = tmp_path / "doc2.pdf"
    test_pdf.touch()
    
    report_file = tmp_path / "_report.json"
    report_file.write_text("[]")
    
    llm_client = MockBypassLLM()
    
    process_unclassified_pdf(tmp_path, llm_client)
    mock_process_pdf.assert_not_called()
    assert llm_client.call_count == 0
