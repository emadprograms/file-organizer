# Quick Task Plan: Batch Copy Documents with Timeline De-duplication

## Objective
Implement Multi-Select "Copy Selected" (نسخ المحدد) allowing documents to be referenced in multiple categories while preventing timeline duplication:
1. `documents` table: Add `is_timeline_visible INTEGER DEFAULT 1` column (1 for primary, 0 for reference copies).
2. `pages` table: Remains pure (1 row per physical page scan with UNIQUE(batch_id, page_number) constraint), avoiding redundant OCR/metadata duplication.
3. Timeline queries: Filter `(is_timeline_visible IS NULL OR is_timeline_visible = 1)` so copied documents do not duplicate timeline entries.
4. Categories queries: Include all documents so copied documents appear in their target category folders.
5. Floating action bar: Add `[ 📋 نسخ المحدد / Copy Selected ]` opening a category selector modal.
6. Backend endpoints in FastAPI and ASP.NET Core: `POST /api/areas/{area}/houses/{house}/documents/batch-copy`.

## Verification & Parity
- Automated Pytest in `tests/test_v14_features.py` (batch-copy endpoint, timeline exclusion, category inclusion).
- Automated xUnit in `web-net/FileOrganizer.Tests/ApiEndpointTests.cs`.
- Automated Vitest in `tests/frontend/components/batch_operations.test.js`.
