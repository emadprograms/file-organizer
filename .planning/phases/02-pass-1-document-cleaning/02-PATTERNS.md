# Phase 2: Pass 1 — Document Cleaning - Patterns

## 1. `src/organize.py` (Modification)
**Role:** Main entry point and CLI coordinator.
**Data Flow:** Parses arguments, validates environment/target, initializes `LLMClient`. Will be extended to load the JSON report, invoke the cleaning logic, and handle the resulting structured state.
**Analog:** The file itself (extends its existing sequential initialization workflow).

**Code Excerpts / Patterns:**
```python
# src/organize.py (Extending the main function)
def main():
    # ... existing initialization and validation ...
    llm_client = LLMClient(api_key=os.getenv("GEMINI_API_KEY"))
    llm_client.default_model = args.model
    
    # NEW: Find JSON path (already verified in validate_target_directory)
    json_path = list(args.target_dir.glob("*_report.json"))[0]
    
    # NEW: Invoke the cleaning phase
    # from src.cleaning import process_cleaning_phase
    # cleaned_pages = process_cleaning_phase(json_path, llm_client)
    
    logger.info("Cleaning phase completed.")
    return 0
```

## 2. `src/cleaning.py` (New File)
**Role:** Implements the core logic for Document Cleaning (CLN-01 to CLN-10). Contains Pydantic data models (`PageData`, `Tenant`), JSON parsing, date inference, string normalization, RapidFuzz matching, LLM canonicalization, timeline bounds calculation, and final page assignment.
**Data Flow:** `Raw JSON Path & LLMClient` -> `Parsing & Normalization` -> `LLM Canonicalization` -> `Timeline Construction` -> `List[PageData]` (Fully resolved).
**Analog:** Uses `pydantic` for modeling (new pattern for this project but standard python) and `src/llm_client.py` for API interactions.

**Code Excerpts / Patterns:**

*Using `LLMClient` with Structured Generation (from `src/llm_client.py` and `google-genai`):*
```python
from google.genai import types

def canonicalize_with_llm(unresolved_names: list[str], llm_client: LLMClient) -> dict[str, str]:
    """Uses the LLMClient to canonicalize tricky tenant names."""
    prompt = f"Map these raw names to canonical tenant names: {unresolved_names}"
    
    # Using **kwargs support in LLMClient.generate_content for config
    response = llm_client.generate_content(
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            # Define response_schema if desired using types.Schema
        )
    )
    # Parse response.text into dict
    # ...
```

*Date inference index proximity logic (Conceptual):*
```python
def infer_dates(pages: list[PageData]):
    """Fills null dates using closest dated page by absolute index (tie-break backward)."""
    # Requires tracking original index from the JSON array
    # 1. Find indices of all pages with valid dates
    # 2. For each null-date page, find min(abs(valid_idx - null_idx))
    # 3. If distances are equal, pick the valid_idx that is < null_idx
    pass
```

*Data Modeling (Conceptual):*
```python
from pydantic import BaseModel
from typing import Optional

class PageData(BaseModel):
    category: str
    content_explanation: str
    expected_tenant_name: Optional[str]
    date: Optional[str]
    sender: str
    receiver: str
    subject: str
    
    # Computed fields after cleaning
    canonical_tenant: Optional[str] = None
    resolved_date: Optional[str] = None
```
