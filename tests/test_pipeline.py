import pytest
from src.pipeline import Pipeline
from src.llm import GemmaClient

@pytest.fixture
def mock_pipeline_with_telemetry():
    import queue
    q = queue.Queue()
    return Pipeline(api_keys=["test-key"]), q

def test_pipeline_integration_stub():
    pass

def test_pipeline_sequential_concurrency(monkeypatch):
    """03-04-03: Fix Concurrency — Sequential Pipeline With Key Rotation."""
    import os
    monkeypatch.setattr(os.path, "exists", lambda x: False)
    from src.pipeline import Pipeline
    from src.ingest import PdfIngestor
    import concurrent.futures
    
    def mock_extract(self, path):
        yield 0, b"page0"
        yield 1, b"page1"
    monkeypatch.setattr(PdfIngestor, "extract_pages_as_images", mock_extract)
    
    pipeline = Pipeline(api_keys=["key1", "key2"])
    
    def mock_classify(image_bytes):
        from src.schemas import PageClassification, Category
        return PageClassification(category=Category.CONTRACT, residents=["John"], date="NONE", house_number="1", summary="test")
    monkeypatch.setattr(pipeline.client, "classify_page", mock_classify)
    monkeypatch.setattr(pipeline.client, "resolve_entities", lambda x: {})
    
    executor_calls = []
    class MockTPE:
        def __init__(self, max_workers=None, **kwargs):
            executor_calls.append(max_workers)
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def submit(self, fn, *args, **kwargs):
            class Fut:
                def result(self): return fn(*args, **kwargs)
            return Fut()
            
    monkeypatch.setattr("src.pipeline.ThreadPoolExecutor", MockTPE)
    monkeypatch.setattr("src.pipeline.as_completed", lambda fs: fs)
    
    pipeline.process_pdf("dummy.pdf")
    
    assert len(executor_calls) > 0
    assert executor_calls[0] == 1, "Should use sequential execution (max_workers=1)"
