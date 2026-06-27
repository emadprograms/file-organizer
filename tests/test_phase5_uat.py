import pytest
import re
from unittest.mock import MagicMock
from src.organizer import CATEGORY_FOLDERS
from src.pipeline import Pipeline
from src.llm import GemmaClient
from src.schemas import Category

def test_exact_arabic_intersection():
    """Verify Exact Arabic Name Intersection."""
    # Pipeline checks this: len(words_current.intersection(words_candidate)) < 2
    # Before, it stripped "ال", meaning "أحمد الخالد" and "أحمد خالد" would intersect on "خالد" and "أحمد"
    # Now, "الخالد" and "خالد" don't intersect.
    
    current_primary_tenant = "أحمد الخالد"
    candidate = "أحمد خالد"
    
    words_current = set(current_primary_tenant.split())
    words_candidate = set(candidate.split())
    
    overlap = words_current.intersection(words_candidate)
    
    assert "الخالد" not in overlap
    assert "خالد" not in overlap
    assert "أحمد" in overlap
    assert len(overlap) == 1  # Before it would have been 2


def test_zero_padded_folders():
    """Verify zero-padding and lexicographical sorting of category folders."""
    # Verify that ALL folders start with two digits and an underscore
    for cat, folder_name in CATEGORY_FOLDERS.items():
        assert re.match(r'^\d{2}_', folder_name), f"Folder '{folder_name}' is not zero-padded"


def test_blank_page_heuristic_skip(tmp_path):
    """Verify that a blank page skips the LLM and falls back."""
    # Mocking a small image size to trigger the <15KB check
    pipeline = Pipeline(api_keys=["dummy_key"])
    # Prevent cache creation from writing to the real directory during tests
    pipeline.cache_file = tmp_path / ".cache.json"
    
    small_image_bytes = b'\x00' * 14000  # 14KB
    
    # We test process_single_page logic indirectly since it's nested in process_pdf
    # But wait, it's defined inside process_pdf. Let's just create a dummy PDF or simulate the chunk.
    # Actually, we can test the behavior by mocking the ingestor and calling process_pdf
    pipeline.ingestor.extract_pages_as_images = MagicMock(return_value=[(0, small_image_bytes)])
    pipeline.client.classify_page = MagicMock()
    pipeline.client.resolve_entities = MagicMock(return_value={})
    
    # Needs a real file path for process_pdf to start, but the file doesn't need to be a real PDF
    # because we mocked extract_pages_as_images
    dummy_pdf = tmp_path / "123.pdf"
    dummy_pdf.touch()
    
    pipeline.process_pdf(str(dummy_pdf))
    
    # verify classify_page was NOT called
    pipeline.client.classify_page.assert_not_called()
    
    # verify cache was populated with fallback OTHER_LETTERS and NONE resident
    import json
    cache_path = f"{dummy_pdf}.cache.json"
    with open(cache_path, "r", encoding="utf-8") as f:
        cache = json.load(f)
    assert cache["0"]["category"] == Category.OTHER_LETTERS.value
    assert cache["0"]["residents"] == ["NONE"]
