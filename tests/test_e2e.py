import pytest
import logging
from unittest.mock import patch
from src.main import main
from src.schemas import DocumentGroup, Category

def test_e2e_pipeline_execution(caplog):
    with patch("src.main.Pipeline") as MockPipeline:
        mock_pipeline_instance = MockPipeline.return_value
        
        mock_docs = [
            DocumentGroup(
                start_page=1,
                end_page=1,
                house_number="123",
                primary_tenant="Test User",
                category=Category.BASIC_DETAILS,
                dates=["2024-01-01"]
            )
        ]
        mock_pipeline_instance.process_pdf.return_value = mock_docs
        
        with patch("sys.argv", ["main.py", "sample.pdf", "-o", "output"]):
            with patch("src.main.FileOrganizer") as MockOrganizer:
                mock_organizer_instance = MockOrganizer.return_value
                mock_organizer_instance.organize.return_value = {"output/123/1_Test User": (1, 1)}
                
                with caplog.at_level(logging.INFO):
                    main()
                    
                for record in caplog.records:
                    assert "UnicodeEncodeError" not in record.message
                    
                mock_organizer_instance.organize.assert_called_once()
                args, kwargs = mock_organizer_instance.organize.call_args
                assert len(args[0]) == 1
                assert args[0][0].primary_tenant == "Test User"
