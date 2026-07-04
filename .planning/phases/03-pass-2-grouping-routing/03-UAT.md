---
status: diagnosed
phase: 03-pass-2-grouping-routing
source: [01-SUMMARY.md, 02-SUMMARY.md, 03-SUMMARY.md, 04-SUMMARY.md, 05-SUMMARY.md, 06-SUMMARY.md]
started: 2026-07-04T17:42:00Z
updated: 2026-07-04T17:42:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Grouping Engine - Category Pre-split
expected: Pages are partitioned into contiguous runs by both category and tenant without crossing boundaries.
result: pass
source: automated
coverage_id: D-01

### 2. Grouping Engine - Overlap Merge
expected: Overlapping chunks correctly merge their boundaries, resolving metadata conflicts in favor of Chunk 1.
result: pass
source: automated
coverage_id: D-02

### 3. Routing Logic - Hardcoded Dictionary
expected: Routing uses a hardcoded dictionary mapping to the 13 topic folders.
result: pass
source: automated
coverage_id: D-03

### 4. Routing Logic - Single Match Direct
expected: Single-match categories bypass the LLM and are routed directly.
result: pass
source: automated
coverage_id: D-04

### 5. Routing Logic - Multi-Match LLM
expected: Multi-match categories use the LLM to route, with fallback to 13_others.
result: pass
source: automated
coverage_id: D-05

### 6. Pipeline Integration - End to End
expected: Running the main CLI with the categorized PDF and JSON report correctly executes Pass 1.5 and Pass 2, producing the organized output folder structure.
result: issue
reported: "Running `python src/main.py pdfs/1273_categorized.pdf` failed during Pass 1 because the Live LLM API returned a 500 error. Additionally, `src/organize.py` (which is supposed to be the CLI entry point for this post-processor) only runs Pass 1 and is not wired to run Pass 2 Grouping & Routing."
severity: blocker

## Summary

total: 6
passed: 5
issues: 1
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Running the main CLI with the categorized PDF and JSON report correctly executes Pass 1.5 and Pass 2, producing the organized output folder structure."
  status: failed
  reason: "User reported: Running `python src/main.py pdfs/1273_categorized.pdf` failed during Pass 1 because the Live LLM API returned a 500 error. Additionally, `src/organize.py` (which is supposed to be the CLI entry point for this post-processor) only runs Pass 1 and is not wired to run Pass 2 Grouping & Routing."
  severity: blocker
  test: 6
  root_cause: "src/organize.py was not updated to instantiate Pipeline, bypass Pass 1, and execute Grouping/Routing. src/main.py requires running Pass 1 which hits an API failure."
  artifacts:
    - path: "src/organize.py"
      issue: "Only calls process_cleaning_phase and stops, does not run Pass 2."
  missing:
    - "Update src/organize.py to run Pass 2 Grouping and Routing (either by calling _group_and_route_documents or configuring Pipeline to skip Pass 1 and run Pass 2)."
  debug_session: ""
