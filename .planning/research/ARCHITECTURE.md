# Architecture Research: Document Processing Pipeline

> Research conducted against PROJECT.md, sample-config.yaml, and 1273_report.json input format, plus industry patterns for two-pass pipelines, centralized API clients, and config-driven routing.

## System Components

### 1. CLI Entry Point (`organize.py`)

The top-level script that:
- Accepts a directory path argument (e.g., `python organize.py ./pdfs/1273`)
- Performs **strict startup validation**: verifies `[ID]_categorized.pdf` and `[ID]_report.json` exist and follow naming conventions
- Loads and **Pydantic-validates** `sample-config.yaml` before any processing
- Derives the house number from the PDF filename
- Orchestrates: Pass 1 → Pass 2 → Output generation

### 2. Config Loader (`config.py`)

Responsible for:
- Loading `sample-config.yaml` using `yaml.safe_load()`
- Validating the entire config against a Pydantic model on startup (fail-fast)
- Exposing typed config objects to the rest of the pipeline: categories, extraction prompts, routing rules, cleaning prompts

The config schema defines:
- **13 categories** with id, name, description
- **Extraction prompt template** and field definitions (residents, category, date, summary)
- **Routing rules** mapping source categories → destination folders (with `allowed_source_categories` per folder)
- **Cleaning prompts** for entity resolution, date outlier detection, semantic grouping

### 3. Report Parser (`report.py`)

Ingests the JSON report from the upstream categorizer. The report format is a dict keyed by **1-indexed page number strings**, where each page has:
- `category`: one of 7 types (forms, letters, id_cards, pictures, utility_bills, contract, others)
- `content_explanation`: verbose description of the page
- Category-specific fields: `name_on_document` (forms), `sender/receiver/subject/date` (letters), `image_contents` (pictures)
- `telemetry`: (currently empty, reserved)

The parser must normalize this into internal `PageData` models for uniform downstream access.

### 4. LLM Client (`llm.py`)

A **centralized singleton** that all LLM calls route through. This is the most critical infrastructure component.

**Rate Limiting:**
- Minimum 7 seconds between requests (simple `time.sleep()` with last-call timestamp tracking)
- No token-bucket needed — the 7s floor is a hard minimum, not a burst allowance

**Error Handling (tiered by HTTP status):**
- `400/404` → Fail fast (bad request, won't improve on retry)
- `500` → Wait 15s, then retry
- `429` → Wait 65s, then retry
- **Boundary detection 500s:** Shrink chunk size after 5 consecutive; hard fail at 10 consecutive
- **Other LLM call 500s:** Skip the item after 5 consecutive
- **429s:** Fail entirely after 3 consecutive (system-level problem)

**Implementation Pattern:**
```python
class LLMClient:
    """Singleton. All LLM calls go through call()."""
    _last_call_time: float = 0
    MIN_INTERVAL: float = 7.0

    def call(self, prompt: str, call_type: str) -> str:
        self._enforce_rate_limit()
        # Error handling varies by call_type
        ...

    def _enforce_rate_limit(self):
        elapsed = time.time() - self._last_call_time
        if elapsed < self.MIN_INTERVAL:
            time.sleep(self.MIN_INTERVAL - elapsed)
        self._last_call_time = time.time()
```

**Model:** Gemma 4 26B A4B IT (all calls use the same model)

### 5. Pass 1: Document Cleaning (`cleaning/`)

Resolves the two critical nulls: **tenant name** and **date**. After Pass 1, every page has both.

**Sub-components:**
- **Anchor Extractor** (`cleaning/anchors.py`): Identifies high-signal documents (contract, forms, id_cards) and extracts tenant names from them. These are the "official" names.
- **Name Canonicalizer** (`cleaning/canonicalize.py`): Uses LLM entity resolution prompt to merge OCR spelling variations. Maps all variants → one canonical name.
- **Tenant Qualifier** (`cleaning/tenants.py`): Applies the threshold: a name becomes a "primary tenant" only if it appears on ≥1 anchor document AND ≥5 total documents after canonicalization.
- **Timeline Builder** (`cleaning/timeline.py`): For each qualified tenant, computes min/max dates from their assigned documents. This timeline becomes the ownership authority.
- **Date Filler** (`cleaning/dates.py`): Pages with null dates inherit from the nearest dated page by position (page index proximity).
- **Tenant Assigner** (`cleaning/assign.py`): Assigns each page to the tenant whose timeline covers the page's date. Overlap periods → earlier tenant wins. Unresolvable → "Unassigned" folder.

### 6. Pass 2: Grouping & Routing (`grouping/`)

Takes the fully-cleaned page list and produces output PDFs in folders.

**Sub-components:**
- **Category Pre-splitter** (`grouping/presplit.py`): Before boundary detection, split the page sequence wherever the category changes. Category change = automatic boundary (no LLM needed).
- **Boundary Detector** (`grouping/boundaries.py`): Within each category-homogeneous run, uses overlapping LLM chunks (pages 1-10, 10-20, 20-30) to detect document boundaries. Overlap pages use set-intersection merge. Boundaries are on subject/topic shift and context/content shift ONLY — date/sender/receiver changes are NOT boundaries.
- **Chunk Merger** (`grouping/merge.py`): Programmatic merge of overlapping chunk results. Verifies: no gaps, no overlaps, no invented pages. Retries on failure.
- **Folder Router** (`grouping/router.py`): Routes document groups to one of 13 destination folders using YAML rules:
  - **Single-match categories** route directly (no LLM): contract→contract, pictures→inspection_and_pictures, id_cards→personal_details, utility_bills→ewa_related_letters
  - **Multi-match categories** (forms, letters, others) use LLM to pick from `allowed_source_categories` list
- **PDF Splitter** (`grouping/split.py`): Uses PyMuPDF to extract page ranges into individual output PDFs.
- **Filename Generator** (`grouping/naming.py`): Uses LLM to generate Arabic summary; combines with date to produce `2026-04-03 - ملخص قصير بالعربية.pdf`.

### 7. Output Builder (`output.py`)

- Creates the output directory structure: `./[source_dir]/output/[House]/[Tenant (timeline)]/[13 folders]`
- All 13 folders created for every tenant, even if empty
- Unassigned documents go to an "Unassigned" folder with inferred period in the name

### 8. Logger (`logger.py`)

- Uses Python's standard `logging` module
- Logs to `./logs/[timestamp]/` at project root
- Full audit trail: every LLM call, every routing decision, every tenant resolution

## Data Flow

```
Input:
  [ID]_categorized.pdf + [ID]_report.json + sample-config.yaml
    │
    ▼
┌─────────────────────────────────────────────┐
│  STARTUP VALIDATION                         │
│  • File existence & naming check            │
│  • Pydantic config validation               │
│  • House number extraction from filename    │
└────────────────────┬────────────────────────┘
                     │
                     ▼
         ┌──── Report Parser ────┐
         │ JSON → list[PageData] │
         │ (raw, with nulls)     │
         └───────────┬───────────┘
                     │
    ═══════════════ PASS 1: CLEANING ═══════════════
                     │
                     ▼
         ┌── Anchor Extraction ──┐
         │ PageData → AnchorNames│
         └───────────┬───────────┘
                     ▼
         ┌── Name Canonicalization ──┐  ← LLM call
         │ AnchorNames + AllNames    │
         │ → NameMapping             │
         └───────────┬───────────────┘
                     ▼
         ┌── Tenant Qualification ──┐
         │ NameMapping → Tenants[]  │
         │ (≥1 anchor + ≥5 docs)   │
         └───────────┬──────────────┘
                     ▼
         ┌── Timeline Building ──┐
         │ Tenants + dates       │
         │ → TenantTimeline[]    │
         └───────────┬───────────┘
                     ▼
         ┌── Date Filling ──────┐
         │ Fill null dates from  │
         │ nearest dated page    │
         └───────────┬──────────┘
                     ▼
         ┌── Tenant Assignment ──┐
         │ Timeline ownership    │
         │ → CleanedPage[]       │
         │ (every page has       │
         │  tenant + date)       │
         └───────────┬───────────┘
                     │
    ═══════════════ PASS 2: GROUPING ═══════════════
                     │
                     ▼
         ┌── Category Pre-split ──┐
         │ CleanedPage[] →        │
         │ CategoryRun[]          │
         └───────────┬────────────┘
                     ▼
         ┌── Boundary Detection ──┐  ← LLM calls (chunked)
         │ Overlapping chunks     │
         │ → RawBoundaries[]      │
         └───────────┬────────────┘
                     ▼
         ┌── Chunk Merge ─────────┐
         │ Programmatic merge     │
         │ → DocumentGroup[]      │
         │ (verified: no gaps,    │
         │  no overlaps)          │
         └───────────┬────────────┘
                     ▼
         ┌── Folder Routing ──────┐  ← LLM calls (multi-match only)
         │ YAML rules + LLM      │
         │ → RoutedGroup[]        │
         └───────────┬────────────┘
                     ▼
         ┌── PDF Splitting ───────┐
         │ PyMuPDF page ranges    │
         └───────────┬────────────┘
                     ▼
         ┌── Filename Generation ─┐  ← LLM call
         │ Arabic summary + date  │
         └───────────┬────────────┘
                     │
    ═══════════════ OUTPUT ═══════════════
                     │
                     ▼
         ┌── Output Builder ──────┐
         │ House/Tenant/Folder    │
         │ structure + PDFs       │
         └────────────────────────┘
```

### Intermediate Data Models (Pydantic)

Stage-specific models — not one giant mutable object:

| Stage | Input Model | Output Model |
|-------|-------------|--------------|
| Report Parse | Raw JSON dict | `PageData` (category, content, name, date — with Optional fields) |
| Anchor Extraction | `list[PageData]` | `AnchorResult` (anchor_names, anchor_pages) |
| Name Canonicalization | `AnchorResult` + all names | `NameMapping` (variant → canonical) |
| Tenant Qualification | `NameMapping` + page counts | `list[QualifiedTenant]` |
| Timeline Building | `list[QualifiedTenant]` + dates | `list[TenantTimeline]` (tenant, start_date, end_date) |
| Date Filling | `list[PageData]` | `list[PageData]` (no more null dates) |
| Tenant Assignment | Pages + timelines | `list[CleanedPage]` (tenant + date guaranteed non-null) |
| Category Pre-split | `list[CleanedPage]` | `list[CategoryRun]` (contiguous same-category pages) |
| Boundary Detection | `CategoryRun` | `list[RawBoundary]` (per chunk) |
| Chunk Merge | `list[RawBoundary]` | `list[DocumentGroup]` (verified page ranges) |
| Folder Routing | `DocumentGroup` + config | `RoutedGroup` (group + destination folder) |
| Filename Gen | `RoutedGroup` | `OutputFile` (path, page_range, filename) |

## Module Structure

```
file-organizer/
├── organize.py              # CLI entry point
├── sample-config.yaml       # YAML routing & prompt configuration
├── .env                     # API keys (GEMINI_API_KEY)
│
├── src/
│   ├── __init__.py
│   ├── config.py            # YAML loading + Pydantic config models
│   ├── schemas.py           # All Pydantic data models
│   ├── report.py            # JSON report parser → list[PageData]
│   ├── llm.py               # Centralized LLM client (singleton, rate limit, retries)
│   ├── output.py            # Directory structure creation + PDF writing
│   ├── logger.py            # Logging setup (./logs/[timestamp]/)
│   │
│   ├── cleaning/            # Pass 1
│   │   ├── __init__.py
│   │   ├── pipeline.py      # Pass 1 orchestrator
│   │   ├── anchors.py       # Anchor document extraction
│   │   ├── canonicalize.py  # LLM name canonicalization
│   │   ├── tenants.py       # Tenant qualification (threshold logic)
│   │   ├── timeline.py      # Min/max date timeline construction
│   │   ├── dates.py         # Null date inference
│   │   └── assign.py        # Timeline-based tenant assignment
│   │
│   └── grouping/            # Pass 2
│       ├── __init__.py
│       ├── pipeline.py      # Pass 2 orchestrator
│       ├── presplit.py      # Category-based pre-splitting
│       ├── boundaries.py    # Overlapping chunk boundary detection
│       ├── merge.py         # Chunk merge + verification
│       ├── router.py        # YAML-driven folder routing
│       ├── split.py         # PyMuPDF page extraction
│       └── naming.py        # LLM Arabic summary filename generation
│
├── tests/
│   ├── test_config.py
│   ├── test_report.py
│   ├── test_llm.py
│   ├── test_cleaning/
│   └── test_grouping/
│
└── logs/                    # Runtime logs (gitignored)
```

## Build Order

### Wave 1: Foundation (no dependencies)
1. **`schemas.py`** — All Pydantic models. Build this first because everything depends on it.
2. **`config.py`** — YAML loading + validation. Needed by everything that reads routing rules.
3. **`logger.py`** — Logging setup. Used everywhere.
4. **`llm.py`** — Centralized LLM client with rate limiting and error handling.

### Wave 2: Input Processing (depends on Wave 1)
5. **`report.py`** — JSON parser. Depends on `schemas.py` for `PageData` model.

### Wave 3: Pass 1 — Cleaning (depends on Wave 1 + 2)
6. **`cleaning/anchors.py`** — Pure logic, no LLM.
7. **`cleaning/canonicalize.py`** — LLM call.
8. **`cleaning/tenants.py`** — Pure logic. Threshold counting.
9. **`cleaning/timeline.py`** — Pure logic. Date math.
10. **`cleaning/dates.py`** — Position-based inference.
11. **`cleaning/assign.py`** — Pure logic. Timeline lookup.
12. **`cleaning/pipeline.py`** — Orchestrator.

### Wave 4: Pass 2 — Grouping (depends on Wave 1 + 3)
13. **`grouping/presplit.py`** — Pure logic.
14. **`grouping/boundaries.py`** — LLM calls.
15. **`grouping/merge.py`** — Pure logic. Set intersection merge.
16. **`grouping/router.py`** — Config lookup + LLM.
17. **`grouping/split.py`** — PyMuPDF.
18. **`grouping/naming.py`** — LLM call.
19. **`grouping/pipeline.py`** — Orchestrator.

### Wave 5: Output + CLI (depends on everything)
20. **`output.py`** — Directory structure builder.
21. **`organize.py`** — CLI entry point.

## LLM Call Inventory

| Call | Module | Frequency | Error Policy |
|------|--------|-----------|-------------|
| Name canonicalization | `cleaning/canonicalize.py` | 1 per house | Skip after 5 consecutive 500s |
| Boundary detection | `grouping/boundaries.py` | N chunks (~pages/10) | Shrink after 5 consecutive 500s, fail at 10 |
| Folder routing (multi-match) | `grouping/router.py` | Per ambiguous group | Skip after 5 consecutive 500s |
| Arabic filename summary | `grouping/naming.py` | Per output document | Skip after 5 consecutive 500s |
