<!-- generated-by: gsd-doc-writer -->
# API Documentation

This document describes the CLI options and key Python programming interfaces provided by `file-organizer`.

## CLI Interface

The primary entry point is `src/main.py`.

### Commands

```bash
python src/main.py create <target_directory> [OPTIONS]
python src/main.py verify <target_directory> [OPTIONS]
python src/main.py reconcile --tenants [OPTIONS]
python src/main.py prepend [OPTIONS]
python src/main.py migrate <target_directory> [OPTIONS]
```

### Common Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--dry-run` | Flag | `False` | Simulates actions (creation, migration) without modifying physical files |
| `--verbose` | Flag | `False` | Enables detailed debug logging |

### `create` Options

| Flag | Type | Default | Description |
|---|---|---|---|
| `--model` | String | `gemini-3.5-flash` | Selects LLM model used for classification, grouping, and cleaning |
| `--routing-model` | String | `gemini-3.5-flash` | Selects LLM model specifically for directory routing |
| `--output-dir` | Path | None | Explicit output directory override |
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

### 3. `State` (`src/core/state.py`)
Unified single-source-of-truth object that manages reading and writing `state.json`.

### 4. `LLMClient` (`src/llm/llm.py`)
Centralized LLM communication handler:
- `generate_content(prompt, model=None)` — Sends structured request to Google Gemini API with built-in retry and exponential backoff logic.

### 5. `FileOrganizer` (`src/timeline/core.py`)
PDF extraction and Vault/Shortcut renderer:
- `organize(documents, house_id, output_dir)` — Extracts page segments, writes them into the `.source_files/vault/`, and generates lightweight `.lnk` shortcuts in categorical folders.
