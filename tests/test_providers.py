import pytest
from unittest.mock import patch, MagicMock
from src.llm.providers import GeminiProvider

def test_gemini_provider_upload_file():
    provider = GeminiProvider("fake_api_key")
    with patch("PIL.Image.open") as mock_open:
        mock_image = MagicMock()
        mock_open.return_value = mock_image
        
        result = provider.upload_file("fake_path.jpg")
        
        mock_open.assert_called_once_with("fake_path.jpg")
        assert result == mock_image

def test_gemini_provider_delete_file():
    provider = GeminiProvider("fake_api_key")
    mock_image = MagicMock()
    provider.delete_file(mock_image)
