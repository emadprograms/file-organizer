# Requirements: File Organizer Post-Processor

**Defined:** 2026-07-03
**Core Value:** Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting.

## v1 Requirements

### Startup & Validation

- [x] **INIT-01**: CLI accepts a single directory path argument (e.g., `python organize.py ./pdfs/1273`)
- [x] **INIT-02**: Fail fast if `[ID]_categorized.pdf` is missing or misnamed in the target directory
- [x] **INIT-03**: Fail fast if `[ID]_report.json` is missing or misnamed in the target directory
- [x] **INIT-04**: Fail fast if required API key (GEMINI_API_KEY) is missing from environment
- [x] **INIT-05**: Derive house number from PDF filename (e.g., `1273_categorized.pdf` → house `1273`)
- [x] **INIT-06**: Create output directory at `./[source_dir]/output/` (same directory as input files)
- [x] **INIT-07**: CLI `--model` flag to switch between `gemma-4-26b-a4b-it` (default) and `gemma-4-31b-it`

### Pass 1 — Document Cleaning

- [x] **CLN-01**: Parse JSON report into internal PageData models with category, content_explanation, expected_tenant_name, date, sender, receiver, subject
- [x] **CLN-02**: Identify anchor documents (categories defined as anchors: contract, forms, id_cards) and extract tenant names from them
- [x] **CLN-03**: Canonicalize tenant names via LLM — merge OCR spelling variations across Arabic and English transliterations into canonical identities
- [x] **CLN-04**: Qualify primary tenants: must appear on ≥1 anchor document AND ≥5 total documents after canonicalization; discard all others
- [x] **CLN-05**: Build tenant timelines from min/max dates of each qualified tenant's assigned documents
- [x] **CLN-06**: Fill null dates by inferring from nearest dated page by position (page index proximity)
- [x] **CLN-07**: Assign each page to the tenant whose timeline covers the page's date; overlap periods → earlier tenant wins
- [x] **CLN-08**: Pages with null tenant AND null date that cannot be resolved go to "Unassigned (inferred period)" folder
- [x] **CLN-09**: One expected_tenant_name per page (or null) — no multi-tenant ambiguity at page level
- [x] **CLN-10**: After Pass 1 completes, every page has a canonical tenant name and a resolved date (except Unassigned)

### Pass 2 — Grouping & Routing

- [x] **GRP-01**: Pre-split page sequence by category — any category change is an automatic document boundary (no LLM needed)
- [x] **GRP-02**: Boundary detection via overlapping chunks (pages 1-10, 10-20, 20-30) with 1-page overlap
- [x] **GRP-03**: LLM grouping rules: boundaries ONLY on subject/topic shift and context/content shift — date changes and sender/receiver changes are NOT boundaries
- [x] **GRP-04**: LLM must provide reasoning for every grouping decision explaining what it saw and what it didn't
- [x] **GRP-05**: LLM returns strict JSON array with start_page, end_page, reason, and brief_arabic_title fields — title generated as part of the grouping call (no separate LLM call)
- [x] **GRP-06**: Programmatic verification of LLM output: no page gaps, no page overlaps, no invented pages; retry on failure
- [x] **GRP-07**: Merge overlapping chunks: if overlap page appears in groups from both chunks, merge those groups into one document
- [x] **GRP-08**: Route documents to folders using hardcoded routing rules — check document's category, find all folders that accept that category
- [x] **GRP-09**: Single-match categories route directly without LLM (contract → 5_contract, pictures → 11_inspection_and_pictures, id_cards → 2_personal_details, utility_bills → 6_ewa_related_letters)
- [x] **GRP-10**: Multi-match categories (forms, letters, others) use LLM to pick from allowed folder list based on content_explanation
- [x] **GRP-11**: Split physical PDF into individual document PDFs using PyMuPDF page ranges
- [x] **GRP-12**: Name output PDFs as `YYYY-MM-DD - brief_arabic_title.pdf` using the title from the grouping LLM call; single-page direct-routed docs (pictures, contracts) get date-only filenames (`YYYY-MM-DD.pdf`)
- [x] **GRP-13**: Dateless documents use inferred date from nearest dated page for filename

### Output Structure

- [ ] **OUT-01**: Create house-level directory from filename (e.g., `1273/`)
- [ ] **OUT-02**: Create tenant-level directories with timeline in name (e.g., `John Doe 2020-2022/`)
- [ ] **OUT-03**: Create all 13 topic subdirectories inside each tenant folder, even if empty
- [ ] **OUT-04**: 13 folders and their allowed categories are hardcoded in Python — routing rules defined as a dictionary in the codebase
- [ ] **OUT-05**: Create "Unassigned (inferred period)" folder for unresolvable documents with inferred period in name
- [ ] **OUT-06**: Page count reconciliation: total pages across all output PDFs must equal total pages in input PDF

### Infrastructure — LLM Client

- [x] **LLM-01**: Centralized LLM client — all calls routed through single class
- [x] **LLM-02**: Model: Gemma 4 26B A4B IT for all calls
- [x] **LLM-03**: Rate limiting: minimum 7 seconds between requests; if reply comes before 7s, wait the remainder; if reply comes after 7s, fire next call immediately
- [x] **LLM-04**: Error 400/404 → fail fast, abort program
- [x] **LLM-05**: Error 500 → wait 15 seconds, retry
- [x] **LLM-06**: Error 429 → wait 65 seconds, retry; fail entirely after 3 consecutive 429s
- [x] **LLM-07**: Boundary detection 500s: shrink chunk size after 5 consecutive; fail at 10 consecutive
- [x] **LLM-08**: Other LLM call 500s: skip item after 5 consecutive, log warning
- [x] **LLM-09**: Error counters reset on ANY successful response

### Infrastructure — Logging & Audit

- [x] **LOG-01**: Timestamped logs directory at project root `./logs/[YYYY-MM-DD_HHMMSS]/`
- [x] **LOG-02**: Full audit trail: every LLM call (prompt + response), every grouping decision, every routing decision, every tenant resolution
- [x] **LOG-03**: All log file handlers use `encoding='utf-8'` for Arabic text
- [ ] **LOG-04**: Reconciliation report at pipeline end: input page count, output file count, pages per file, unaccounted pages

### Infrastructure — File System Safety

- [x] **FS-01**: Sanitize Arabic filenames: strip Windows-reserved characters, invisible Unicode control characters
- [x] **FS-02**: Truncate filenames to 200 characters to leave margin for path prefixes (Windows MAX_PATH)
- [x] **FS-03**: Unicode normalize all filenames with `NFC` before any file operation
- [x] **FS-04**: Atomic file writes: write to temp file, then rename to final path

### Differentiators

- [x] **DIFF-01**: Dry run / preview mode (`--dry-run` flag) — show full pipeline output (folder structure, file names, routing decisions) without writing any files
- [ ] **DIFF-02**: Checkpoint/resume — persist Pass 1 cleaned state to disk so Pass 2 can resume after crash without re-running Pass 1
- [ ] **DIFF-03**: Reconciliation manifest — output a detailed manifest comparing every input page to its output location

## v2 Requirements

### Enhanced Processing

- **ENH-01**: Batch processing mode — process multiple house directories in sequence
- **ENH-02**: Configurable chunk size for boundary detection (currently hardcoded at 10)
- **ENH-03**: 2-page overlap option for boundary detection (currently 1-page)

## Out of Scope

| Feature | Reason |
|---------|--------|
| GUI or web interface | CLI-only tool for specific government workflow |
| Real-time / streaming processing | Batch tool, one house at a time |
| Custom ML model training | LLM handles OCR noise better than limited training data |
| Document Management System features | Filesystem IS the storage layer |
| Multi-user / concurrent access | Single operator, single invocation |
| Async LLM calls | 7s rate limit makes async pointless |
| AI extraction / PDF categorization | Handled by separate categorizer repo |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INIT-01 | Phase 1 | Complete |
| INIT-02 | Phase 1 | Complete |
| INIT-03 | Phase 1 | Complete |
| INIT-04 | Phase 1 | Complete |
| INIT-05 | Phase 1 | Complete |
| INIT-06 | Phase 1 | Complete |
| CLN-01 | Phase 2 | Complete |
| CLN-02 | Phase 2 | Complete |
| CLN-03 | Phase 2 | Complete |
| CLN-04 | Phase 2 | Complete |
| CLN-05 | Phase 2 | Complete |
| CLN-06 | Phase 2 | Complete |
| CLN-07 | Phase 2 | Complete |
| CLN-08 | Phase 2 | Complete |
| CLN-09 | Phase 2 | Complete |
| CLN-10 | Phase 2 | Complete |
| GRP-01 | Phase 3 | Complete |
| GRP-02 | Phase 3 | Complete |
| GRP-03 | Phase 3 | Complete |
| GRP-04 | Phase 3 | Complete |
| GRP-05 | Phase 3 | Complete |
| GRP-06 | Phase 3 | Complete |
| GRP-07 | Phase 3 | Complete |
| GRP-08 | Phase 3 | Complete |
| GRP-09 | Phase 3 | Complete |
| GRP-10 | Phase 3 | Complete |
| GRP-11 | Phase 3 | Complete |
| GRP-12 | Phase 3 | Complete |
| GRP-13 | Phase 3 | Complete |
| OUT-01 | Phase 4 | Pending |
| OUT-02 | Phase 4 | Pending |
| OUT-03 | Phase 4 | Pending |
| OUT-04 | Phase 4 | Pending |
| OUT-05 | Phase 4 | Pending |
| OUT-06 | Phase 4 | Pending |
| LLM-01 | Phase 1 | Complete |
| LLM-02 | Phase 1 | Complete |
| LLM-03 | Phase 1 | Complete |
| LLM-04 | Phase 1 | Complete |
| LLM-05 | Phase 1 | Complete |
| LLM-06 | Phase 1 | Complete |
| LLM-07 | Phase 1 | Complete |
| LLM-08 | Phase 1 | Complete |
| LLM-09 | Phase 1 | Complete |
| LOG-01 | Phase 1 | Complete |
| LOG-02 | Phase 1 | Complete |
| LOG-03 | Phase 1 | Complete |
| LOG-04 | Phase 4 | Pending |
| FS-01 | Phase 1 | Complete |
| FS-02 | Phase 1 | Complete |
| FS-03 | Phase 1 | Complete |
| FS-04 | Phase 1 | Complete |
| DIFF-01 | Phase 5 | Complete |
| DIFF-02 | Phase 4 | Pending |
| DIFF-03 | Phase 4 | Pending |

**Coverage:**

- v1 requirements: 47 total
- Mapped to phases: 47
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-03*
*Last updated: 2026-07-03 after initial definition*
