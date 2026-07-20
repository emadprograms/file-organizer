import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.categorization.categorization import process_unclassified_pdf
from src.llm.llm import LLMClient
from src.core.schemas import CategorizationResult

class MockCrashLLM(LLMClient):
    def __init__(self):
        # Dummy initialization to avoid env var checks
        pass
        
    @property
    def provider(self):
        return MagicMock()

    def upload_file(self, file_path):
        return MagicMock(name="uploaded_file")
        
    def delete_file(self, file_obj):
        pass

    def generate_content(self, contents, response_schema=None, **kwargs):
        if not hasattr(self, 'call_count'):
            self.call_count = 0
        self.call_count += 1
        
        if self.call_count == 5:
            raise KeyboardInterrupt("Simulated crash on 5th call (page 2, 1st call)")
            
        dummy_data = {
            "category": "contract",
            "content_explanation": "Mock explanation",
            "expected_tenant_name": "Mock Tenant",
            "expected_house_number": "123",
            "date": "2023-01-01"
        }
        
        # Filter dummy_data to only keys present in the schema
        if response_schema:
            schema_keys = response_schema.model_fields.keys()
            filtered_data = {k: v for k, v in dummy_data.items() if k in schema_keys}
            return response_schema(**filtered_data)
        
        return CategorizationResult(**dummy_data)

@patch("src.categorization.categorization.process_pdf")
@patch("cv2.imread")
@patch("PIL.Image.open")
def test_process_unclassified_pdf_checkpointing(mock_pil, mock_imread, mock_process_pdf, tmp_path):
    """
    Test that process_unclassified_pdf properly checkpoints progress incrementally.
    We simulate a PDF with 5 pages and crash the LLM on the 3rd page.
    """
    # 1. Setup mock PDF and target directory
    test_pdf = tmp_path / "test.pdf"
    test_pdf.touch()
    
    tmp_pdf_dir = tmp_path / ".tmp_test"
    tmp_pdf_dir.mkdir()
    
    # Create fake images so os.path.exists passes
    for i in range(5):
        (tmp_pdf_dir / f"page_{i}.png").touch()
        
    # Mock process_pdf to return a status dict with 5 extracted pages
    mock_status = {
        f"page_{i}": {"status": "extracted"} for i in range(5)
    }
    mock_process_pdf.return_value = (mock_status, str(tmp_pdf_dir))
    
    # Mock image reading to avoid actual file I/O
    mock_imread.return_value = None
    mock_pil.return_value = MagicMock()
    
    llm_client = MockCrashLLM()
    
    # 2. Run the process, expect it to crash on the 3rd page (page_2)
    with pytest.raises(KeyboardInterrupt):
        process_unclassified_pdf(tmp_path, llm_client)
        
    # 3. Verify progress.json was saved incrementally
    progress_file = tmp_pdf_dir / "progress.json"
    assert progress_file.exists(), "progress.json should have been written"
    
    with open(progress_file, "r") as f:
        data = json.load(f)
        
    # page_0 and page_1 should be classified, the rest should be 'extracted'
    assert data["page_0"]["status"] == "classified"
    assert data["page_1"]["status"] == "classified"
    assert data["page_2"]["status"] == "extracted"
    assert data["page_3"]["status"] == "extracted"
    assert data["page_4"]["status"] == "extracted"
    
    # 4. Resume processing
    # When resumed, process_pdf will load progress.json and return the updated status
    # We'll just patch process_pdf to return `data` as if it loaded it
    mock_process_pdf.return_value = (data, str(tmp_pdf_dir))
    
    # Reset LLM to not crash, just count calls
    class MockResumeLLM(LLMClient):
        def __init__(self): pass
        @property
        def provider(self): return MagicMock()

        def upload_file(self, file_path):
            return MagicMock(name="uploaded_file")
            
        def delete_file(self, file_obj):
            pass

        def generate_content(self, contents, response_schema=None, **kwargs):
            if not hasattr(self, 'call_count'):
                self.call_count = 0
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
            
    resume_llm = MockResumeLLM()
    process_unclassified_pdf(tmp_path, resume_llm)
    
    # 5. Verify the resume only processed the remaining 3 pages (2 calls per page)
    assert getattr(resume_llm, 'call_count', 0) == 6, "Should only make LLM calls for the remaining 3 pages (2 calls each)"
    
    # 6. Verify final report was created properly
    report_file = tmp_path / "test_report.json"
    assert report_file.exists()
    with open(report_file, "r") as f:
        report_data = json.load(f)
    
    # Must be a list (as per our previous bug fix)
    assert isinstance(report_data, list)
    assert len(report_data) == 5
    assert report_data[0]["status"] == "classified"
    assert report_data[4]["status"] == "classified"
    assert report_data[0]["category"] == "contract"
