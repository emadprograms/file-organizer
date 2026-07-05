---
status: issues
files_reviewed: 4
critical: 0
blocker: 0
warning: 1
info: 1
total: 2
---

# Code Review: Phase 04

## Findings

### WR-01: Unclosed PyMuPDF Document in organize.py
**Severity:** Warning
**File:** `src/organize.py`

**Description:**
The PDF document is opened to retrieve the page count using `fitz.open(str(pdf_path)).page_count`, but the document object is never explicitly closed. This leaks a file descriptor, relying on Python's garbage collector to eventually close it.

**Recommendation:**
Use a context manager (`with` statement) to ensure the document is properly closed:
```python
with fitz.open(str(pdf_path)) as pdf_doc:
    total_input_pages = pdf_doc.page_count
```

### IN-01: Inconsistent Checkpoint File Locations
**Severity:** Info
**File:** `src/organize.py`

**Description:**
The Pass 1 checkpoint (`{house_id}_cleaned.json`) is placed directly in the `output/` directory, while the Pass 2 checkpoint (`grouped.json`) is placed in an `output/checkpoints/` subdirectory.

**Recommendation:**
Consider moving the Pass 1 checkpoint to the `checkpoints` directory as well for better organization and consistency.
