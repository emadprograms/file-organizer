# Phase 2: Pass 1 — Document Cleaning - Discussion Log

**Date:** 2026-07-03

## 1. Name Canonicalization Strategy
- **Presented:** LLM Only, RapidFuzz + LLM, Other
- **Selected:** RapidFuzz + LLM
- **Notes:** Leverages RapidFuzz for obvious typos and LLM for complex translations.

## 2. Null Date Inference
- **Presented:** Look backward first, Closest absolute distance, Other
- **Selected:** Closest absolute distance
- **Notes:** Tie-breaks backward if distances are equal.

## 3. Unassigned Folder Naming
- **Presented:** Year only, Year-Month, Full Date Range, Other
- **Selected:** Year-Month
- **Notes:** E.g., "Unassigned (2020-05)".
