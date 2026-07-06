# Phase 09 Patterns: final-e2e-sweep-fix-absolute-pdf-indexing-array-bounds-align

## 1. `src/core/indexing.py` (New File or modified `src/core/utils.py`)
**Role:** Centralized utility module for indexing. Handles bounds resolution and 0-based conversions securely.
**Data Flow:** Provides utility methods to convert 1-based indices to 0-based, and validate bounds given a max length.
**Closest Analog:** `src/core/utils.py` (Data sanitization and parsing utilities).
**Concrete Code Excerpt:**
```python
# from src/core/utils.py
def sanitize_filename(name: str, max_length: int = 50) -> str:
    # ...
```

## 2. `src/logger.py`
**Role:** Logging subsystem. Needs updates to support writing detailed LLM requests/responses to separate JSON files inside `logs/traces/` and tracking token usage.
**Data Flow:** Invoked by LLM clients and main application logic to log operations. Creates `.json` and `.error.json` traces.
**Closest Analog:** Existing `setup_logging` and `log_llm_api_call` in `src/logger.py`.
**Concrete Code Excerpt:**
```python
# from src/logger.py
def setup_logging(run_id: str = None, verbose: bool = False) -> str:
    # ...
    
def log_llm_api_call(request: dict, response: dict, run_id: str):
    # ...
```

## 3. `src/llm/llm.py`
**Role:** Centralized LLM client (`LLMClient`).
**Data Flow:** Handles API requests. Needs updates to parse token usage metadata, print it at INFO level, and write trace/error JSON files via the updated logger.
**Closest Analog:** `LLMClient._route_llm_call`.
**Concrete Code Excerpt:**
```python
# from src/llm/llm.py
    def _route_llm_call(self, model: str, contents: list, response_schema: type | None = None, log_prefix: str = "Retry", max_attempts: Optional[int] = None) -> Any:
        # ...
```

## 4. `src/processing/pipeline.py`
**Role:** Main processing pipeline orchestrator.
**Data Flow:** Passes raw pages through vision extraction, interpolation, grouping, and routing. Needs updates to enforce Pass 1 date resolution, strict array bounds validation before slicing/indexing, and final reconciliation checks.
**Closest Analog:** `process_pdf` and `_interpolate_dates`.
**Concrete Code Excerpt:**
```python
# from src/processing/pipeline.py
    def process_pdf(self, pdf_path: str, config_path: str = "sample-config.yaml") -> list[DocumentGroup]:
        # ...
        if len(raw_pages) != total_expected_pages:
            raise RuntimeError(f"CRITICAL: Expected {total_expected_pages} pages, but only recovered {len(raw_pages)}. Aborting Pass 1.5 to prevent data loss.")
```

## 5. `src/processing/split.py`
**Role:** PDF splitting and page extraction logic.
**Data Flow:** Receives requests to extract page segments. Needs strict array bounds validation before triggering `fitz.insert_pdf` slicing.
**Closest Analog:** `extract_pdf_segment`.
**Concrete Code Excerpt:**
```python
# from src/processing/split.py
def extract_pdf_segment(source_pdf: str, start_page: int, end_page: int, output_path: str):
    # ...
    # insert_pdf arguments: from_page and to_page are 0-indexed and inclusive
    dst_doc.insert_pdf(src_doc, from_page=start_page, to_page=end_page)
```

## 6. `src/processing/routing.py`
**Role:** Determines the destination folder for each document group.
**Data Flow:** Receives a DocumentGroup and selects a folder. Needs safe runtime defaults to catch out-of-bounds or failed indices, routing them to "Unassigned" rather than crashing.
**Closest Analog:** `route_document`.
**Concrete Code Excerpt:**
```python
# from src/processing/routing.py
def route_document(group: DocumentGroup, llm_client: Any) -> tuple[str, bool]:
    # ...
    global consecutive_routing_failures
    if consecutive_routing_failures >= 5:
        log.warning("Skipping LLM routing due to 5 consecutive failures.")
        return "13_others", False
```

## 7. `tests/*`
**Role:** Validation architecture for the newly introduced bug fixes.
**Data Flow:** Validates components. Need `tests/test_indexing.py` (bounds/conversions), `tests/test_llm.py` (tracing logs/tokens), and integration updates in `tests/test_pipeline.py`.
