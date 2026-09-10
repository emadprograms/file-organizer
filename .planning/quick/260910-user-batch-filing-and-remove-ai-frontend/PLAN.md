# Quick Task: Multi-File Batch Filing & Remove AI Features From Frontend

## Description
Transform the Ingest Station frontend into a 100% deterministic, user-controlled system by removing all AI autofill buttons, preview endpoints, and AI references, and replacing batch ingestion with a modern multi-file batch filing queue supporting multi-document assignment and single-document broadcasting to multiple houses.

## Goals
1. **Remove Frontend AI References & Calls**:
   - Completely eliminate `#btn-ingest-autofill` button, AI descriptions, AI category suggestions, and calls to `/api/ingest/preview-ai`.
   - Ensure frontend ingestion is 100% deterministic, user-driven, and offline-capable without AI dependencies.
2. **Modern Multi-File Batch Filing Queue**:
   - Mode Switcher bar (`Single Document` vs `Batch Filing`).
   - Shared Category (`#ingest-batch-category-select`), Shared Date (`#ingest-batch-date-select`), and Shared Area (`#ingest-batch-area-select`).
   - Queue list showing dropped/selected PDF files with editable titles (auto-filled from filename).
   - Auto-detection of house numbers from filenames (e.g., `514`, `house 500`) against available houses in the active area.
   - Automatic selection of the latest active or latest ended tenant for detected houses.
3. **Single Document Broadcasting Across Multiple Houses**:
   - Allow users to click `+ Add House` on any document card in the batch queue to assign that same document to additional houses.
   - Automatically populates the target house's latest tenant.
4. **Sequential Batch Ingestion Execution**:
   - Sequentially submits each task via `POST /api/ingest` with `mode="manual"`.
   - Live progress indicator showing file count, percentage, and progress bar.
   - Comprehensive error handling, success toast, automatic modal close, and view refresh.
5. **Full Test Suite & .NET Parity**:
   - Vitest component tests covering all batch filing flows and asserting absence of AI buttons.
   - Playwright E2E test suite (`tests/frontend/test_ingest_batch_playwright.py`) validating mode switching, AI absence, multi-file queue processing, and broadcasting.
   - Pytest API tests in `tests/test_ingest_api.py` validating multi-house manual ingest.
   - Sync static files to `web-net/wwwroot/` via `dotnet build` and verify `FileOrganizer.Tests`.
