# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-03)

**Core value:** Automatically transform a flat, pre-categorized PDF into a perfectly organized folder structure per tenant, with zero manual sorting.
**Current focus:** Phase 1 — Foundation & Infrastructure

## Current Status

- **Active Phase:** Phase 1 — Foundation & Infrastructure
- **Phase Status:** Not Started
- **Blockers:** None

## Phase Progress

| Phase | Name | Status | Plans |
|-------|------|--------|-------|
| 1 | Foundation & Infrastructure | ○ Pending | 0/0 |
| 2 | Pass 1 — Document Cleaning | ○ Pending | 0/0 |
| 3 | Pass 2 — Grouping & Routing | ○ Pending | 0/0 |
| 4 | Output Structure & Reconciliation | ○ Pending | 0/0 |
| 5 | Dry Run & Polish | ○ Pending | 0/0 |

## Decision Log

| Date | Decision | Context |
|------|----------|---------|
| 2026-07-03 | Two-pass architecture (Clean → Group) | Pass 1 guarantees clean data for Pass 2 |
| 2026-07-03 | Anchor-based tenant resolution | High-signal docs only; 5-doc + 1-anchor threshold |
| 2026-07-03 | Overlapping chunks for boundary detection | 1-page overlap with set-intersection merge |
| 2026-07-03 | Subject/content shift as ONLY boundary signal | Date/sender changes are metadata, not boundaries |
| 2026-07-03 | Hardcoded routing rules | Dropped YAML config — simpler, suits the structure |
| 2026-07-03 | Timeline as ownership authority | Overlap periods → earlier tenant |
| 2026-07-03 | Arabic filename from grouping call | No separate LLM call — title piggybacks on boundary detection |
| 2026-07-03 | Gemma 4 26B A4B IT (default) with --model flag for 31B | CLI flag for model switching |

---
*Last updated: 2026-07-03 after project initialization*
