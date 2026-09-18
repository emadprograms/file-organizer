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

---

## Web API Interface

The .NET Kestrel server (`web-net`) and Python FastAPI server (`src/api`) expose identical REST endpoints.

### Search API (`GET /api/search?q={query}&limit={limit}`)

Performs high-performance unified search across houses, tenants, documents, and individual page records.

- **Query Parameters:**
  - `q` (string): Search query (house ID, Latin transliterated name, Arabic name, category, or keyword).
  - `limit` (int, optional): Maximum results to return (default: `50`).

- **Tenant Matching & Ranking Engine:**
  - **Transliteration Normalization:** Normalizes English digraphs and vowels (`ee` $\to$ `y`, `oo` $\to$ `w`, `v` $\to$ `w`) to align Latin transliterations with Arabic script phonetics.
  - **Article Stripping:** Automatically handles definite articles (`al-`, `al `, `al`, `ال`) so queries like `balushi` and `al balushi` match `البلوشي` identically.
  - **Token-Level Matching:** Evaluates individual name tokens to prevent substring false positives (e.g. searching `ameed` correctly matches `عميد` without falsely matching common names like `أحمد` or `محمد`).
  - **Relevance Scoring:**
    - Substring matches: Score 1000+
    - Exact word transliteration match: Score 500-600
    - Phonetic token match: Score 400
    - Token prefix match: Score 300
  - **Tenure Duration & Status Badges:**
    - `is_current` (boolean): `true` if the tenant currently resides in the property (`end_date` is `null` or `Present`), otherwise `false`.
    - `duration_category` (string, optional): `"short"` (< 5 years), `"medium"` (5–10 years), or `"long"` (> 10 years) for currently residing tenants; `null` for past tenants.

### Document Page Manipulation APIs

#### 1. Reorder Document Pages (`POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/reorder-pages`)
Physically reorders the pages of a PDF in the vault based on a sequence of 1-based page numbers. Also available via `/api/documents/{vaultId}/reorder-pages`.

- **Request Body (`application/json`):**
  ```json
  {
    "page_order": [4, 5, 1, 2, 3],
    "rotations": { "4": 90 }
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Pages reordered successfully",
    "vault_id": "doc_12345",
    "page_count": 5
  }
  ```

#### 2. Rotate Document Pages (`POST /api/areas/{areaId}/houses/{houseId}/documents/{vaultId}/rotate-pages`)
Rotates specific pages of a PDF by a given angle (default 90° clockwise) and permanently rewrites the PDF to disk. Also available via `/api/documents/{vaultId}/rotate-pages`.

- **Request Body Options (`application/json`):**
  - **Option A (Pages list format):**
    ```json
    {
      "pages": [1, 3],
      "angle": 90
    }
    ```
  - **Option B (Rotations dictionary format):**
    ```json
    {
      "rotations": {
        "1": 90,
        "3": 90
      }
    }
    ```
  - **Option C (Combined format for max compatibility):**
    ```json
    {
      "rotations": { "1": 90, "3": 90 },
      "pages": [1, 3],
      "angle": 90
    }
    ```
- **Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "vault_id": "doc_12345",
    "page_count": 5,
    "rotations": {
      "1": 90,
      "3": 90
    }
  }
  ```

---

### UI Component: Document Page Editor (`#doc-page-editor-modal`)
The Document Page Editor provides a high-comfort visual canvas for editing, rotating, deleting, extracting, and reordering document pages:
- **Responsive Card Zoom:**
  - Zoom levels: 70%, 85%, 100% (default), 120%, 145%, 175%, 210%.
  - Controls: Dedicated `+` / `-` / `100%` buttons in the modal header, keyboard shortcuts (`Ctrl +`, `Ctrl -`, `Ctrl 0`), and `Ctrl + Scroll` wheel gestures.
  - Dynamic Grid: CSS Grid with `repeat(auto-fill, minmax(min(100%, var(--editor-card-min-width)), var(--editor-card-max-width)))` and `justify-content: center` ensures single-page, two-page, and multi-page documents scale smoothly and never distort or blow up to fill 1000px uncontrollably.
  - Fluid Canvas: Canvases scale fluidly with CSS `object-fit: contain` and auto-re-render sharp high-DPI bitmaps upon zoom stabilization.
- **Page Rotation:**
  - 1-tap `↻ 90°` button directly on each page card header for immediate individual page rotation.
  - Multi-page "Rotate 90° (تدوير 90°)" button in bottom toolbar for rotating all selected pages simultaneously.
  - Permanent PDF rewrite via `RotatePagesAsync` with immediate cache-busted viewer sync.



