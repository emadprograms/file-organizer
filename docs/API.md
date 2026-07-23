<!-- generated-by: gsd-doc-writer -->
# API Documentation

This document describes the CLI options and key Python programming interfaces provided by `file-organizer`.

## CLI Interface

The primary entry point is `src/main.py`.

### Positional Arguments & Commands

```bash
python src/main.py <target_directory> [OPTIONS]
python src/main.py create <target_directory> [OPTIONS]
python src/main.py append [OPTIONS]
python src/main.py reconcile --tenants <tenants_file> [OPTIONS]
```

### Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `target_dir` | Path | (Required for default mode) | Path to target directory containing PDF and JSON report files |
| `--dry-run` | Flag | `False` | Simulates file organization and prints summary without modifying files |
| `--model` | String | `gemini-3.1-flash-lite` | Selects LLM model used for classification, grouping, and cleaning |
| `--routing-model` | String | `google/gemma-4-31b-it` | Selects LLM model specifically for directory routing |
| `--output-dir` | Path | None | Explicit output directory override |
| `--verbose` | Flag | `False` | Enables detailed debug logging |
| `--skip-llm` | Flag | `False` | Skips LLM calls (useful in mock/testing environments) |

---

## Python Data Contracts

### 1. `PageData` (`src/core/models.py`)
Represents single PDF page metadata extracted from raw JSON reports:
- `page_num`: int — 1-based index of the page.
- `document_type`: str — Primary document type or category.
- `date`: Optional[str] — Formatted date string (YYYY-MM-DD) if extracted.
- `canonical_tenant`: Optional[str] — Standardized tenant/resident name.

### 2. `DocumentGroup` (`src/core/schemas.py`)
Represents a cohesive set of pages forming a single document:
- `house_id`: str — Unique property identifier.
- `category`: str — Category classification.
- `tenant_name`: str — Assigned canonical tenant.
- `page_numbers`: list[int] — Sequence of 1-based page numbers.
- `start_date`: Optional[str] — Start date of document.
- `end_date`: Optional[str] — End date of document.

### 3. `LLMClient` (`src/llm/llm.py`)
Centralized LLM communication handler:
- `generate_content(prompt, model=None)` — Sends structured request to Google Gemini API with built-in retry and exponential backoff logic.

### 4. `FileOrganizer` (`src/timeline/core.py`)
PDF extraction and physical folder structure renderer:
- `organize(documents, house_id, output_dir)` — Extracts page segments, writes individual document PDFs, compiles TOC, and compresses finalized PDF output.
