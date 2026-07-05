# Roadmap: File Organizer Post-Processor

**Created:** 2026-07-03
**Phases:** 5
**Structure:** Horizontal Layers (Foundation → Pass 1 → Pass 2 → Output → Polish)

---

## Milestone: v1.0

### Phase 1: Foundation & Infrastructure

**Goal:** Build the shared infrastructure that every other module depends on — schemas, LLM client, logging, CLI entry point, and file system utilities.

**Requirements:** INIT-01, INIT-02, INIT-03, INIT-04, INIT-05, INIT-06, INIT-07, LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06, LLM-07, LLM-08, LLM-09, LOG-01, LOG-02, LOG-03, FS-01, FS-02, FS-03, FS-04

**Success Criteria:**

1. `python organize.py ./pdfs/1273` validates file pair existence and exits cleanly with error if missing
2. `python organize.py ./pdfs/1273 --model gemma-4-31b-it` accepts model flag
3. Centralized LLM client enforces 7s rate limit between calls (measurable via timestamps in logs)
4. LLM client handles 400→fail, 500→retry 15s, 429→retry 65s with correct consecutive error counting
5. Timestamped log directory created at `./logs/YYYY-MM-DD_HHMMSS/` with UTF-8 encoding
6. Filename sanitizer strips Windows-reserved chars, truncates to 200 chars, NFC normalizes
7. JSON report parsed into Pydantic PageData models

### Phase 2: Pass 1 — Document Cleaning

**Goal:** Implement the full cleaning pipeline — anchor extraction, name canonicalization, tenant qualification, timeline building, date filling, and tenant assignment. After this phase, every page has a canonical tenant and a resolved date.

**Requirements:** CLN-01, CLN-02, CLN-03, CLN-04, CLN-05, CLN-06, CLN-07, CLN-08, CLN-09, CLN-10

**Success Criteria:**

1. Anchor documents (contract, forms, id_cards) correctly identified from the JSON report
2. LLM canonicalization merges OCR variations (Arabic + English transliterations) into canonical identities
3. Tenant qualification filters out names that appear on <1 anchor OR <5 total documents
4. Timeline generated with correct min/max dates per qualified tenant
5. All null dates filled via nearest-dated-page inference
6. All pages assigned to a tenant (or explicitly to Unassigned bucket)
7. Zero null tenant names and zero null dates in the cleaned output (except Unassigned)

### Phase 3: Pass 2 — Grouping & Routing

**Goal:** Implement boundary detection with overlapping chunks, programmatic verification, chunk merging, folder routing, and PDF splitting. After this phase, the original PDF is split into logical documents and each is assigned a destination folder.

**Requirements:** GRP-01, GRP-02, GRP-03, GRP-04, GRP-05, GRP-06, GRP-07, GRP-08, GRP-09, GRP-10, GRP-11, GRP-12, GRP-13

**Success Criteria:**

1. Category pre-split correctly produces automatic boundaries at every category change
2. Overlapping chunks (1-10, 10-20, etc.) with 1-page overlap processed correctly
3. LLM grouping uses ONLY subject/content shift as boundary signals (not date or sender changes)
4. LLM response includes reasoning and brief_arabic_title for every group
5. Programmatic verification catches gaps, overlaps, and invented pages — retries on failure
6. Overlap merge correctly joins groups that share the overlap page
7. On 500 errors: chunk size shrinks (10→5→3) after 5 consecutive; hard fail at 10
8. Single-match categories route directly without LLM; multi-match categories use LLM
9. PyMuPDF splits PDF into individual document files by page ranges
10. Filenames follow `YYYY-MM-DD - عنوان عربي.pdf` format (or `YYYY-MM-DD.pdf` for direct-routed)

### [x] Phase 4: Output Structure & Reconciliation

**Goal:** Build the final output directory hierarchy, move split PDFs into their assigned folders, run page count reconciliation, and implement checkpoint/resume and reconciliation manifest.

**Requirements:** OUT-01, OUT-02, OUT-03, OUT-04, OUT-05, OUT-06, LOG-04, DIFF-02, DIFF-03

**Success Criteria:**

1. Output directory created at `./[source_dir]/output/[house_number]/`
2. Tenant directories include timeline in name (e.g., `John Doe 2020-2022/`)
3. All 13 topic subdirectories created for every tenant, even if empty
4. Routing rules hardcoded as Python dict — forms/letters/others routed correctly
5. Unassigned folder created with inferred period when needed
6. Page count reconciliation passes: total input pages == sum of output PDF pages
7. Pass 1 checkpoint saved to disk; Pass 2 can resume from checkpoint after crash
8. Reconciliation manifest generated showing every input page → output file mapping

### Phase 5: Dry Run & Polish

**Goal:** Implement dry run mode, final integration testing, and edge case hardening.

**Requirements:** DIFF-01

**Success Criteria:**

1. `--dry-run` flag shows full pipeline output (folder structure, filenames, routing decisions) without writing any files
2. End-to-end test with real `1273_report.json` and `1273_categorized.pdf` produces correct output
3. Arabic filenames render correctly on Windows
4. All error paths tested (missing files, LLM failures, malformed JSON)

### Phase 6: Milestone 1.0 Audit Gap Closures

**Goal:** Resolve integration gaps found in the v1.0 Milestone Audit to ensure full pipeline correctness across phase boundaries.

**Requirements:** CLN-02, CLN-04, CLN-08, OUT-05, OUT-03, FS-04, LOG-04, GRP-04, GRP-12, LLM-08

**Success Criteria:**

1. Anchor category mismatch is resolved in `pipeline.py` to match JSON report categories.
2. The 13 topic subdirectories are proactively created for every tenant, not just dynamically.
3. Unassigned folder is correctly named `Unassigned (inferred period)` instead of `NONE`.
4. Checkpoints and fallbacks use atomic temporary-file-and-rename writes.
5. The reconciliation report detailed breakdown is logged to console/logs.
6. Grouping LLM prompt explicitly instructs reasoning generation.
7. Direct-routed documents check if they are single-page before receiving date-only names.
8. 5-consecutive failure tracking is implemented for non-boundary multi-match LLM calls in `routing.py`.

---

## Phase Dependencies

```
Phase 1 (Foundation) ──→ Phase 2 (Pass 1) ──→ Phase 3 (Pass 2) ──→ Phase 4 (Output) ──→ Phase 5 (Polish) ──→ Phase 6 (Gap Closures)
```

All phases are strictly sequential — each depends on the previous.

---

## Requirement Coverage

| 01 | Requirements & Architecture | Complete | 2026-07-04 | 1 | 1 |
| 02 | Parsing & Pass 1 Cleaning | Complete | 2026-07-04 | 2 | 2 |
| 03 | Pass 2 Grouping & Routing | Complete | 2026-07-04 | 2 | 2 |
| 04 | Output Structure & Reconciliation | Complete | 2026-07-05 | 2 | 2 |
| 05 | Dry Run & Polish | Pending | - | 0 | 0 |

| Requirement | Phase |
|-------------|-------|
| INIT-01 through INIT-07 | Phase 1 |
| LLM-01 through LLM-09 | Phase 1 |
| LOG-01 through LOG-03 | Phase 1 |
| FS-01 through FS-04 | Phase 1 |
| CLN-01 through CLN-10 | Phase 2 |
| GRP-01 through GRP-13 | Phase 3 |
| OUT-01 through OUT-06 | Phase 4 |
| LOG-04 | Phase 4 |
| DIFF-02, DIFF-03 | Phase 4 |
| DIFF-01 | Phase 5 |

**Coverage:** 48/48 requirements mapped ✓
**Unmapped:** 0 ✓

### Phase 7: Cross-Phase Integration Fixes — tenant/date mapping, relative indexing, CLI flags, dry-run safety

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 6
**Plans:** 0 plans

Plans:

- [ ] TBD (run /gsd-plan-phase 7 to break down)

### [x] Phase 8: Address tech debt: test assertions for logs/fallback

**Goal:** Address tech debt: test assertions for logs/fallback
**Requirements**: Verify fallback/retry logic emits correct log warnings
**Depends on:** Phase 7
**Plans:** 4 plans

Plans:

- [x] 1. Upgrade Log Levels in `llm.py`
- [x] 2. Add Caplog Assertions to Fallback Tests
- [x] 3. Add Caplog Assertions to LLM Retry Tests
- [x] 4. Verify the Test Suite Passes

### Phase 9: Final E2E Sweep: Fix absolute PDF indexing, array bounds alignment, resolved dates, LLM logging, and pipeline architecture

**Goal:** Final E2E Sweep: Fix absolute PDF indexing, array bounds alignment, resolved dates, LLM logging, and pipeline architecture
**Requirements**: CLN-08, GRP-06, LOG-02, OUT-06
**Depends on:** Phase 8
**Plans:** 1/1 plans complete

Plans:

- [ ] 1. Core Implementation and Verification

---
*Roadmap created: 2026-07-03*
*Last updated: 2026-07-03 after initial creation*
