import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.categorization.categorization import process_unclassified_pdf
from src.llm.llm import LLMClient
from src.core.schemas import CategorizationResult

class MockExtractLLM(LLMClient):
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
        dummy_data = {
            "category": "contract",
            "content_explanation": "Mock explanation",
            "expected_tenant_name": "Mock Tenant",
            "expected_house_number": "123",
            "date": "2023-01-01"
        }
        if response_schema:
            schema_keys = response_schema.model_fields.keys()
            filtered_data = {k: v for k, v in dummy_data.items() if k in schema_keys}
            return response_schema(**filtered_data)
        
        return CategorizationResult(**dummy_data)

@patch("src.categorization.categorization.process_pdf")
@patch("cv2.imread")
@patch("PIL.Image.open")
def test_cat_01_extracts_metadata_and_copies_pdf(mock_pil, mock_imread, mock_process_pdf, tmp_path):
    """
    Test CAT-01: System can extract structured metadata (_report.json) 
    from a raw PDF document using OCR and Gemini 3.1 Flash Lite.
    """
    test_pdf = tmp_path / "testdoc.pdf"
    test_pdf.touch()
    
    tmp_pdf_dir = tmp_path / ".tmp_testdoc"
    tmp_pdf_dir.mkdir()
    
    # Fake one page
    (tmp_pdf_dir / "page_0.png").touch()
    
    mock_status = {
        "page_0": {"status": "extracted"}
    }
    mock_process_pdf.return_value = (mock_status, str(tmp_pdf_dir))
    mock_imread.return_value = None
    mock_pil.return_value = MagicMock()
    
    llm_client = MockExtractLLM()
    
    process_unclassified_pdf(tmp_path, llm_client)
    
    report_file = tmp_path / "testdoc_report.json"
    categorized_file = tmp_path / "testdoc_categorized.pdf"
    
    assert report_file.exists(), "_report.json should be created"
    assert categorized_file.exists(), "_categorized.pdf should be copied"
    
    with open(report_file, "r") as f:
        data = json.load(f)
        
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["category"] == "contract"
    assert data[0]["status"] == "classified"
