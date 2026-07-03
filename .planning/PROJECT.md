# File Organizer Post-Processor

## What This Is

A CLI-based post-processing tool that takes pre-categorized housing PDFs and their corresponding JSON reports, resolves tenant identities, groups pages into logical multi-page documents, and organizes them into a structured directory hierarchy: House → Tenant (with timeline) → 13 Topic Folders. Built for the Kingdom of Bahrain Ministry of Interior housing document workflow.

## Core Value

Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting — driven entirely by the JSON report data, LLM intelligence, and configurable YAML routing rules.

## Requirements

### Validated

- [x] CLI script that takes a directory path (e.g., `python organize.py ./pdfs/1273`) (Validated in Phase 01: foundation-infrastructure)
- [x] Strict startup validation: fail fast if `[ID]_categorized.pdf` or `[ID]_report.json` is missing or misnamed (Validated in Phase 01: foundation-infrastructure)
- [x] Output directory at `./[source_dir]/output/` (Validated in Phase 01: foundation-infrastructure)
- [x] Logs directory at project root `./logs/[timestamp]/` with full audit trail (Validated in Phase 01: foundation-infrastructure)
- [x] Centralized LLM client: all calls routed through single class enforcing rate limits and error handling (Validated in Phase 01: foundation-infrastructure)
- [x] LLM model: Gemma 4 26B A4B IT (Validated in Phase 01: foundation-infrastructure)
- [x] Rate limiting: minimum 7 seconds between requests (Validated in Phase 01: foundation-infrastructure)
- [x] Error handling: 400/404 → fail fast; 500 → wait 15s retry; 429 → wait 65s retry (Validated in Phase 01: foundation-infrastructure)
- [x] Boundary detection 500s: shrink chunk after 5 consecutive, fail at 10 consecutive (Validated in Phase 01: foundation-infrastructure)
- [x] Other LLM calls 500s: skip after 5 consecutive (Validated in Phase 01: foundation-infrastructure)
- [x] 429s: fail entirely after 3 consecutive (Validated in Phase 01: foundation-infrastructure)

## Current State

Phase 01 complete — Built the shared filesystem utilities and logging infrastructure, and the core CLI entry point.

### Active

- [ ] Pydantic validation of `sample-config.yaml` format on startup before any processing
- [ ] YAML-driven folder routing: 13 folders, each with `allowed_source_categories` — zero hardcoded routing rules
- [ ] Pass 1 — Document Cleaning: resolve tenant names, fill null dates, build timelines
- [ ] Pass 2 — Grouping & Routing: boundary detection via overlapping LLM chunks, folder assignment, PDF splitting
- [ ] Anchor-based tenant resolution using high-signal documents (contract, forms, id_cards)
- [ ] LLM-driven name canonicalization to merge OCR spelling variations
- [ ] Primary tenant qualification: must appear on ≥1 anchor document AND ≥5 total documents after canonicalization
- [ ] Timeline generation from min/max dates of a tenant's assigned documents
- [ ] Timeline-based ownership: documents assigned to tenant whose timeline covers the document's date; overlap → earlier tenant
- [ ] Null tenant/date resolution: infer from nearest dated page by position; if unresolvable → Unassigned folder with inferred period in name
- [ ] Boundary detection with overlapping chunks (pages 1-10, 10-20, 20-30) and programmatic merge on overlap page
- [ ] LLM grouping rules: boundaries on subject/topic shift and context/content shift ONLY — date and sender/receiver changes are NOT boundaries
- [ ] LLM must provide reasoning for every grouping decision
- [ ] Programmatic verification of LLM grouping output: no gaps, no overlaps, no invented pages; retry on failure
- [ ] Pre-split by category before boundary detection (category change = automatic boundary)
- [ ] Folder routing: single-match categories route directly (no LLM); multi-match categories use LLM to pick from allowed list
- [ ] Output PDFs named as `2026-04-03 - ملخص قصير بالعربية.pdf` (date + brief Arabic summary from LLM)
- [ ] Dateless documents use inferred date from nearest dated page
- [ ] All 13 folders created for every tenant, even if empty
- [ ] One `expected_tenant_name` per page (or null) — no multi-tenant ambiguity per page
- [ ] PyMuPDF for PDF splitting by page ranges

### Out of Scope

- AI extraction or PDF categorization from scratch — relies on outputs from the separate categorizer repo
- Batch processing multiple houses — one house directory at a time
- GUI — CLI only
- House number extraction — always derived from the PDF filename

## Context

- The categorizer (separate repo) already processes each PDF page through an LLM and produces a JSON report with: category (one of 7: forms, letters, id_cards, pictures, utility_bills, contract, others), content_explanation, expected_tenant_name, date/sender/receiver/subject (for letters), and other category-specific fields.
- Documents are housing-related: contracts, government letters, utility bills, ID cards, inspection photos, maintenance forms — all in Arabic.
- The 7 broad categories from the categorizer must map to 13 specific destination folders via YAML configuration.
- Folder routing rules (which category can go where):
  - **forms** → basic_details, ewa, rent_deduction, maintenance, others
  - **letters** → allocation_order, key_handover, ewa_related_letters, rent_deduction, allowance_deduction, notifications, maintenance, inspection_and_pictures, modifications, others
  - **utility_bills** → ewa_related_letters only
  - **contract** → contract only
  - **pictures** → inspection_and_pictures only
  - **id_cards** → personal_details only
  - **others** → NOT basic_details, NOT allocation_order, NOT contract (can go to remaining folders)

## Constraints

- **Model**: Gemma 4 26B A4B IT — all LLM calls use this model
- **Rate Limit**: Minimum 7 seconds between LLM requests, enforced centrally
- **Single Processing**: No batch mode — one house directory per invocation
- **Compatibility**: Must consume the JSON report format from the existing categorizer without modification
- **Language**: Output filenames and LLM summaries in Arabic

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-pass architecture (Clean → Group) | Pass 1 guarantees every page has a tenant + date before Pass 2 runs, eliminating null-handling complexity in grouping/routing | — Pending |
| Anchor-based tenant resolution | Pulling names from every page creates noise (maintenance workers, clerks); anchor documents (contracts, forms, IDs) are the most reliable sources | — Pending |
| 5-document + 1-anchor threshold | Filters out incidental names that appear once or twice without being overly aggressive | — Pending |
| Overlapping chunks for boundary detection | Simple 1-page overlap with set-intersection merge avoids complex state machines and sliding window prompts | — Pending |
| Subject/content shift as ONLY boundary signal | Date changes and sender/receiver changes are metadata, not boundaries — a back-and-forth exchange about the same issue is one document | — Pending |
| YAML for routing rules, hardcode engineering decisions | Routing rules are business logic that changes; rate limits and error handling are engineering constants | — Pending |
| Timeline as ownership authority | Single source of truth for document ownership; overlap periods → earlier tenant | — Pending |
| Centralized LLM client | One place to enforce rate limiting, error handling, and logging across all call types | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-03 after Phase 01 completion*
