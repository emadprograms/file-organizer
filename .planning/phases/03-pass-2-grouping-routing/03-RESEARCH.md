# Phase 03: Pass 2 — Grouping & Routing - Research

**Researched:** 2026-07-04
**Domain:** PDF document grouping, LLM-based boundary detection, folder routing
**Confidence:** HIGH

## Summary

Phase 3 implements the second pass of the document processing pipeline: taking the cleaned page sequence from Pass 1 (where every page has a canonical tenant and resolved date) and dividing it into multi-page logical documents. The phase has three major subsystems: (1) boundary detection using overlapping LLM chunks with programmatic verification, (2) hardcoded folder routing with LLM fallback for ambiguous categories, and (3) physical PDF splitting via PyMuPDF.

The codebase already has the infrastructure needed — `LLMClient` with provider failover, `extract_pdf_segment` for PDF splitting, `DocumentGroup` dataclass, and the `FileOrganizer` skeleton. The main work is replacing the current declarative grouping/routing strategies with the new LLM-driven overlapping-chunk approach and hardcoded 13-folder routing logic.

**Primary recommendation:** Build the chunking engine and verification loop as a standalone module (`src/processing/grouping.py`), add routing logic as a new module (`src/processing/routing.py`), extend `DocumentGroup` with new fields (`reason`, `brief_arabic_title`, `folder_path`), and wire everything through `pipeline.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Trust the chunk where the document started (Chunk 1) for resolving disagreements on the overlap page — it has the context of the document's origin.
- **D-02:** If the LLM fails to pick a valid folder for ambiguous documents (like letters or forms), retry the LLM call once with stricter constraints. If it still fails, fallback to the generic "others" sub-folder.
- **D-03:** If the LLM returns valid JSON but repeatedly fails the programmatic gap/overlap verification, treat it like a 500 error: shrink the chunk size and retry, failing the pipeline after 10 total attempts.

### Agent's Discretion
None specified — all major decisions are locked.

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Category pre-split | Processing (Python) | — | Pure data partitioning, no LLM needed |
| Overlapping chunk generation | Processing (Python) | — | Deterministic sliding window algorithm |
| LLM boundary detection | LLM Client | Processing | LLM decides boundaries; processing validates |
| Programmatic verification | Processing (Python) | — | Gap/overlap/invented-page checks are deterministic |
| Overlap merge | Processing (Python) | — | Deterministic join logic on shared pages |
| Folder routing (single-match) | Processing (Python) | — | Direct dictionary lookup, no LLM |
| Folder routing (multi-match) | LLM Client | Processing | LLM picks folder; processing handles fallback |
| PDF splitting | Processing (PyMuPDF) | — | Already implemented in `split.py` |
| Filename generation | Processing (Python) | — | Date formatting + Arabic title from LLM output |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pymupdf` (fitz) | ≥1.28.0 | PDF splitting by page ranges | Already in project; `extract_pdf_segment` exists [VERIFIED: codebase] |
| `google-genai` | ≥2.10.0 | LLM calls for grouping and routing | Already in project via `LLMClient` [VERIFIED: codebase] |
| `pydantic` | ≥2.13.4 | Response schemas for LLM structured output | Already in project for schemas [VERIFIED: codebase] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tenacity` | ≥9.1.4 | Retry logic for LLM calls | Already used in providers.py [VERIFIED: codebase] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hardcoded routing dict | YAML config routing | User decided hardcoded (PROJECT.md constraint) |
| Custom chunk retry | tenacity decorator | Custom needed because chunk-shrink logic (10→5→3) is domain-specific |

**Installation:** No new packages needed — all dependencies already installed.

## Architecture Patterns

### System Architecture Diagram

```
Pass 1 Output (raw_pages with tenant + date)
    │
    ▼
┌─────────────────────────┐
│  Category Pre-Split     │  Split into contiguous same-category runs
│  (GRP-01)               │
└──────────┬──────────────┘
           │ list[CategoryRun]
           ▼
┌─────────────────────────┐
│  Overlapping Chunk Gen  │  Yield chunks of N pages with 1-page overlap
│  (GRP-02)               │
└──────────┬──────────────┘
           │ list[Chunk]
           ▼
┌─────────────────────────────────────────┐
│  LLM Grouping Loop (per chunk)          │
│  ┌─────────────┐  ┌──────────────────┐  │
│  │ LLM Call     │→│ Verify Response   │  │
│  │ (GRP-03/04/05)│ │ (GRP-06)         │  │
│  └─────────────┘  └──────┬───────────┘  │
│       ▲                   │ fail         │
│       └───────────────────┘ (shrink)     │
│  On 500: shrink chunk (10→5→3) (GRP-07) │
└──────────┬──────────────────────────────┘
           │ list[RawGroup] per chunk
           ▼
┌─────────────────────────┐
│  Overlap Merge          │  Join groups sharing overlap page
│  (GRP-07, D-01)         │  Trust Chunk 1 for overlap page
└──────────┬──────────────┘
           │ list[MergedGroup]
           ▼
┌─────────────────────────────────────┐
│  Folder Routing                      │
│  Single-match → direct (GRP-09)      │
│  Multi-match → LLM + retry (GRP-10)  │
│  Fallback → "others" (D-02)          │
└──────────┬──────────────────────────┘
           │ list[RoutedDocument]
           ▼
┌─────────────────────────┐
│  PDF Split & Name       │  PyMuPDF extract_pdf_segment
│  (GRP-11, GRP-12/13)    │  YYYY-MM-DD - عنوان.pdf
└─────────────────────────┘
```

### Recommended Project Structure
```
src/
├── processing/
│   ├── grouping.py      # NEW: chunk generator, LLM grouping loop, verification, merge
│   ├── routing.py       # NEW: 13-folder routing dict, single/multi-match logic
│   ├── pipeline.py      # MODIFY: wire Pass 2 using grouping.py + routing.py
│   ├── organizer.py     # MODIFY: accept routed documents, use new naming convention
│   └── split.py         # EXISTING: extract_pdf_segment (no changes needed)
├── core/
│   └── schemas.py       # MODIFY: extend DocumentGroup, add GroupingResponse schema
└── llm/
    └── llm.py           # MODIFY: add group_chunk() and route_document() methods
```

### Pattern 1: Overlapping Chunk Generator
**What:** Sliding window that yields page subsequences with 1-page overlap
**When to use:** Processing any category run longer than chunk_size
**Example:**
```python
# [ASSUMED] — standard sliding window pattern
def generate_chunks(pages: list, chunk_size: int = 10, overlap: int = 1):
    """Yield overlapping chunks from a page sequence."""
    if len(pages) <= chunk_size:
        yield pages, False  # single chunk, no overlap to merge
        return
    start = 0
    while start < len(pages):
        end = min(start + chunk_size, len(pages))
        yield pages[start:end], start > 0
        if end >= len(pages):
            break
        start = end - overlap  # 1-page overlap
```

### Pattern 2: Chunk-Shrink Retry Loop
**What:** Retry LLM calls with progressively smaller chunks on repeated failures
**When to use:** When LLM returns 500s or fails verification
**Example:**
```python
# [ASSUMED] — domain-specific retry pattern from CONTEXT.md D-03
CHUNK_SIZES = [10, 5, 3]
MAX_CONSECUTIVE_FAILURES = 5
MAX_TOTAL_FAILURES = 10

def process_with_shrink(pages, llm_client):
    consecutive_failures = 0
    total_failures = 0
    chunk_size_idx = 0
    
    while total_failures < MAX_TOTAL_FAILURES:
        chunk_size = CHUNK_SIZES[chunk_size_idx]
        chunks = list(generate_chunks(pages, chunk_size))
        # ... process chunks, on failure:
        consecutive_failures += 1
        total_failures += 1
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            chunk_size_idx = min(chunk_size_idx + 1, len(CHUNK_SIZES) - 1)
            consecutive_failures = 0
    raise RuntimeError("Hard fail: 10 consecutive failures")
```

### Anti-Patterns to Avoid
- **Using date/sender as boundary signals:** CONTEXT.md explicitly forbids this — only subject/content shift matters (GRP-03)
- **Separate LLM call for titles:** The `brief_arabic_title` must come from the grouping call itself (GRP-05), not a follow-up call
- **YAML-based routing:** The routing rules are hardcoded in Python (PROJECT.md constraint), not loaded from config
- **Async LLM calls:** The 7s rate limit makes async pointless (Out of Scope)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF page extraction | Custom page-by-page copy | `extract_pdf_segment` in `split.py` | Already handles compression, temp files, error recovery |
| LLM provider failover | Manual retry loops | `LLMClient._route_llm_call` | Already implements 429/500 handling, provider rotation |
| Filename sanitization | Custom regex | `utils.sanitize_filename` | Already handles Arabic, Windows reserved chars, path length |
| Date normalization | Custom parsing | `utils.normalize_date` | Already in codebase |

**Key insight:** Most infrastructure is already built. This phase is about _using_ existing infrastructure with new domain logic (grouping + routing), not building new infrastructure.

## Common Pitfalls

### Pitfall 1: Off-by-one in Overlap Merge
**What goes wrong:** Groups from adjacent chunks double-count or skip the overlap page
**Why it happens:** The overlap page appears in both chunks; naive concatenation duplicates it
**How to avoid:** When merging, if the last group of Chunk N and the first group of Chunk N+1 share the overlap page, merge those groups into one. Always trust Chunk 1's metadata (D-01).
**Warning signs:** Total page count after merge ≠ total input pages

### Pitfall 2: Verification Accepts Invented Pages
**What goes wrong:** LLM returns page numbers outside the actual chunk range
**Why it happens:** LLM hallucination — it may invent page indices it wasn't given
**How to avoid:** Verification must check that ALL returned page indices are within the chunk's actual range, not just contiguity
**Warning signs:** Page numbers in response > max page in chunk

### Pitfall 3: Category Pre-split Creates Too Many Tiny Runs
**What goes wrong:** Single-page category changes create runs too small for meaningful grouping
**Why it happens:** OCR misclassification in Pass 1 creates spurious category changes
**How to avoid:** Each category run, even if 1 page, is a valid document boundary. Don't try to merge runs of different categories — that contradicts GRP-01.
**Warning signs:** Many single-page documents in output (acceptable if categories genuinely alternate)

### Pitfall 4: Routing LLM Gets Confused by Arabic Content
**What goes wrong:** LLM picks wrong folder for multi-match categories
**Why it happens:** Arabic OCR text can be noisy; content_explanation may be vague
**How to avoid:** Provide the full list of allowed folders in the prompt with clear descriptions. Retry once with stricter constraints (D-02). Fallback to "others" on second failure.
**Warning signs:** Documents consistently landing in "others" folder

## Code Examples

### 13-Folder Routing Dictionary
```python
# [ASSUMED] — derived from REQUIREMENTS.md GRP-08/GRP-09/GRP-10
FOLDER_ROUTING: dict[str, list[str]] = {
    "1_requests_and_applications": ["forms"],
    "2_personal_details": ["id_cards"],
    "3_housing_committee_decisions": ["letters"],
    "4_financial_details": ["forms", "letters"],
    "5_contract": ["contract"],
    "6_ewa_related_letters": ["utility_bills"],
    "7_maintenance": ["forms", "letters"],
    "8_complaints_and_violations": ["letters", "forms"],
    "9_legal_correspondence": ["letters"],
    "10_ministry_internal_memos": ["letters"],
    "11_inspection_and_pictures": ["pictures"],
    "12_tenant_correspondence": ["letters"],
    "13_others": ["others", "forms", "letters"],  # catch-all
}

# Reverse index: category → list of folders that accept it
CATEGORY_TO_FOLDERS: dict[str, list[str]] = {}
for folder, cats in FOLDER_ROUTING.items():
    for cat in cats:
        CATEGORY_TO_FOLDERS.setdefault(cat, []).append(folder)

# Single-match categories (GRP-09)
SINGLE_MATCH = {cat for cat, folders in CATEGORY_TO_FOLDERS.items() if len(folders) == 1}
# Multi-match categories (GRP-10)  
MULTI_MATCH = {cat for cat, folders in CATEGORY_TO_FOLDERS.items() if len(folders) > 1}
```

### LLM Grouping Response Schema
```python
# [ASSUMED] — derived from GRP-05
from pydantic import BaseModel, Field

class GroupEntry(BaseModel):
    start_page: int = Field(description="First page index of this document group (0-indexed)")
    end_page: int = Field(description="Last page index of this document group (0-indexed, inclusive)")
    reason: str = Field(description="Why these pages belong together — what subject/content connects them")
    brief_arabic_title: str = Field(description="Short Arabic title describing this document group")

class GroupingResponse(BaseModel):
    groups: list[GroupEntry] = Field(description="Array of document groups found in this chunk")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Declarative grouping (group_by fields) | LLM-based boundary detection with chunks | Phase 3 | Enables multi-page document detection across subject boundaries |
| Config-driven YAML routing | Hardcoded 13-folder Python routing | Phase 3 | Faster, no config parsing, domain-specific logic |
| Single tenant per DocumentGroup | Tenant already resolved in Pass 1 | Phase 2 | Simplifies grouping — tenant is input, not output |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 13-folder routing dictionary structure matches actual ministry folders | Code Examples | Documents routed to wrong folders — easily corrected by updating dict |
| A2 | Chunk size starts at 10 pages | Architecture Patterns | Performance impact only — configurable |
| A3 | `extract_pdf_segment` uses 0-indexed inclusive page ranges | Don't Hand-Roll | Off-by-one errors in PDF splitting — verified from split.py source |
| A4 | `brief_arabic_title` is generated by the grouping LLM call, not separately | Architecture Patterns | Extra LLM call would be wasteful — confirmed by GRP-05 |

## Open Questions (RESOLVED)

1. **Exact 13-folder names and category mappings**
   - What we know: GRP-09 lists 4 single-match categories (contract, pictures, id_cards, utility_bills) with their target folders
   - What's unclear: The exact names and category mappings for the remaining 9 folders
   - Recommendation: Define as a Python dict in `routing.py`; user can review during execution
   - RESOLVED: [decision] We will implement the dictionary as defined in the Code Examples section. The user can adjust the dictionary mapping later if needed, but it satisfies the requirement to hardcode the routing logic.

2. **Date format for dateless documents (GRP-13)**
   - What we know: Inferred date from nearest dated page should be used
   - What's unclear: Whether the inferred date is already populated on the page data from Pass 1.5
   - Recommendation: Pass 1.5 already fills null dates via `_fill_missing_dates` — verify this during implementation
   - RESOLVED: [decision] Pass 1.5 handles global date interpolation, so we can rely on `doc.dates[0]` representing the best available date. If no date is available, we will fallback to the literal string `"nodate"` in the filename.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GRP-01 | Pre-split page sequence by category — any category change is an automatic document boundary | Category Pre-Split in Architecture Patterns; pure Python partitioning |
| GRP-02 | Boundary detection via overlapping chunks (1-10, 10-20) with 1-page overlap | Overlapping Chunk Generator pattern; sliding window algorithm |
| GRP-03 | LLM grouping: boundaries ONLY on subject/content shift — NOT date/sender changes | Anti-Patterns section; explicit in LLM prompt constraints |
| GRP-04 | LLM must provide reasoning for every grouping decision | GroupingResponse schema includes `reason` field |
| GRP-05 | LLM returns strict JSON with start_page, end_page, reason, brief_arabic_title | GroupingResponse Pydantic schema; structured output via google-genai |
| GRP-06 | Programmatic verification: no gaps, no overlaps, no invented pages; retry on failure | Verification logic in Architecture Diagram; Pitfall 1 & 2 |
| GRP-07 | Merge overlapping chunks: shared overlap page → merge groups | Overlap Merge in Architecture Diagram; D-01 trust Chunk 1 |
| GRP-08 | Route documents using hardcoded routing rules | 13-Folder Routing Dictionary code example |
| GRP-09 | Single-match categories route directly without LLM | SINGLE_MATCH set derived from CATEGORY_TO_FOLDERS |
| GRP-10 | Multi-match categories use LLM to pick folder | MULTI_MATCH set; LLM routing with retry + fallback (D-02) |
| GRP-11 | Split physical PDF using PyMuPDF page ranges | `extract_pdf_segment` in split.py — already implemented |
| GRP-12 | Name output PDFs as `YYYY-MM-DD - brief_arabic_title.pdf` | Filename generation from GroupingResponse data |
| GRP-13 | Dateless documents use inferred date from nearest dated page | Pass 1.5 `_fill_missing_dates` already populates dates |
</phase_requirements>

## Project Constraints (from GEMINI.md)

- **Model:** Gemma 4 26B A4B IT — all LLM calls use this model
- **Rate Limit:** Minimum 7 seconds between LLM requests, enforced centrally
- **Single Processing:** No batch mode — one house directory per invocation
- **Language:** Output filenames and LLM summaries in Arabic
- **LLM SDK:** Use `google-genai` (NOT the deprecated `google-generativeai`)
- **No async:** Async for LLM calls is explicitly out of scope
- **YAML:** Always use `yaml.safe_load()` — never `yaml.load()`

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already installed, used across 15+ test files) |
| Config file | None explicit — pytest auto-discovers `tests/` directory |
| Quick run command | `python -m pytest tests/test_pipeline.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GRP-01 | Category pre-split produces boundaries at every category change | unit | `python -m pytest tests/test_grouping.py::test_category_presplit -x` | ❌ Wave 0 |
| GRP-02 | Overlapping chunks generated correctly (1-10, 10-20, etc.) | unit | `python -m pytest tests/test_grouping.py::test_chunk_generator_overlap -x` | ❌ Wave 0 |
| GRP-03 | LLM prompt enforces subject-only boundaries (mock LLM) | unit | `python -m pytest tests/test_grouping.py::test_boundary_signals -x` | ❌ Wave 0 |
| GRP-04 | LLM response includes reasoning field | unit | `python -m pytest tests/test_grouping.py::test_response_has_reasoning -x` | ❌ Wave 0 |
| GRP-05 | LLM response validates against GroupingResponse schema | unit | `python -m pytest tests/test_grouping.py::test_schema_validation -x` | ❌ Wave 0 |
| GRP-06 | Verification catches gaps, overlaps, invented pages | unit | `python -m pytest tests/test_grouping.py::test_verification_logic -x` | ❌ Wave 0 |
| GRP-07 | Overlap merge joins groups sharing overlap page | unit | `python -m pytest tests/test_grouping.py::test_overlap_merge -x` | ❌ Wave 0 |
| GRP-08 | Routing dict maps categories to correct folders | unit | `python -m pytest tests/test_routing.py::test_routing_dict -x` | ❌ Wave 0 |
| GRP-09 | Single-match categories route without LLM | unit | `python -m pytest tests/test_routing.py::test_single_match_direct -x` | ❌ Wave 0 |
| GRP-10 | Multi-match categories use LLM with retry/fallback | unit | `python -m pytest tests/test_routing.py::test_multi_match_llm -x` | ❌ Wave 0 |
| GRP-11 | PDF split produces correct page ranges | integration | `python -m pytest tests/test_split.py -x` | ✅ Exists |
| GRP-12 | Filename follows `YYYY-MM-DD - عنوان.pdf` format | unit | `python -m pytest tests/test_routing.py::test_filename_format -x` | ❌ Wave 0 |
| GRP-13 | Dateless documents use inferred date | unit | `python -m pytest tests/test_routing.py::test_dateless_filename -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_grouping.py tests/test_routing.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_grouping.py` — covers GRP-01 through GRP-07 (chunk generation, verification, merge)
- [ ] `tests/test_routing.py` — covers GRP-08 through GRP-10, GRP-12, GRP-13 (routing, naming)
- [ ] Fixtures: mock `PageData` objects with category/date/tenant, mock `LLMClient` responses

*(Existing `tests/test_split.py` and `tests/test_pipeline.py` cover PDF splitting infrastructure)*

## Security Domain

> This phase does not introduce new authentication, session management, access control, or cryptography concerns. The primary security-relevant area is input validation of LLM responses.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | yes | Pydantic schema validation of LLM responses; programmatic verification of page ranges |
| V6 Cryptography | no | N/A |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| LLM response injection (invented pages) | Tampering | Programmatic verification: all page indices must exist in chunk range |
| Path traversal via Arabic filenames | Tampering | `utils.sanitize_filename` strips reserved chars; `os.path.basename` on folder names |
| DoS via infinite retry loop | Denial of Service | Hard fail at 10 consecutive failures; chunk-shrink circuit breaker |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `src/processing/pipeline.py`, `src/processing/split.py`, `src/processing/organizer.py`, `src/core/schemas.py`, `src/llm/llm.py` — verified existing infrastructure
- `REQUIREMENTS.md` — GRP-01 through GRP-13 requirement definitions
- `CONTEXT.md` — D-01, D-02, D-03 locked decisions

### Secondary (MEDIUM confidence)
- `GEMINI.md` / `.agents/GEMINI.md` — project constraints and technology stack

### Tertiary (LOW confidence)
- 13-folder names and exact category mappings — assumed from GRP-09 examples, needs user confirmation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, verified from codebase
- Architecture: HIGH — clear requirements, existing infrastructure mapped
- Pitfalls: MEDIUM — overlap merge edge cases need careful implementation
- Validation: HIGH — pytest infrastructure exists, test map is straightforward

**Research date:** 2026-07-04
**Valid until:** 2026-08-04 (stable domain, no external API changes expected)
