---
status: resolved
trigger: "User reported: house batch doesn't make any sense. It is asking shared category? what? there are many documents for that one house. there are several categories that is the point (for that one house). I think house batch (the last one) is not done properly."
created: 2026-09-10
updated: 2026-09-10
---

# Debug Session: House Batch Per-File Category Redesign

## Symptoms
- **Reported behavior**: In Ingest Station's "House Batch (Multiple files → 1 house)" mode, the UI asks for a single "Shared Category" at the top card, forcing all uploaded documents for that house into the exact same category.
- **Expected behavior**: In House Batch, a user is organizing multiple diverse documents for ONE house (e.g. lease contract, utility bills, personal IDs, maintenance invoices). Each document in the batch queue must have its own **Category selector** (and document date), rather than being forced into a single shared category.
- **Root Cause**: In `src/api/static/index.html` lines 834-858 and `src/api/static/js/ingest-station.js`, House Batch was designed with a top-level `housebatch-category-select` and `housebatch-date-select`, and each file card in `renderHouseBatchQueue` only had a title input without a per-document category select or date picker. `submitHouseBatchIngest` was passing the same top-level `category` to all files.

## Resolution
1. **Frontend HTML (`src/api/static/index.html`)**:
   - Removed the top-level "Shared Category" select (`#housebatch-category-select`) and "Shared Primary Date" input (`#housebatch-date-select`).
   - Cleaned the top header card to focus exclusively on destination targeting: Target Area (`#housebatch-area-select`), Target House (`#housebatch-house-select`), and Assigned Tenant (`#housebatch-tenant-select`).
2. **Ingest Station Script (`src/api/static/js/ingest-station.js`)**:
   - Implemented `detectCategoryFromFilename(filename)` covering 10 keyword patterns with smart Arabic and English normalization (contracts, utilities, maintenance, personal ID, handover, allocation, notices, deductions, modifications, photos/inspections, and fallback `13 - رسائل متنوعة`).
   - Updated `addFilesToHouseBatch` to initialize each queue item with its detected category (`detectCategoryFromFilename`) and date (`getTodayIsoDate()`).
   - Updated `renderHouseBatchQueue()` to render each document card with:
     - Document title input (`.housebatch-title-input`)
     - Category dropdown (`.housebatch-category-select`) populated with all 13 standard Arabic categories, defaulting to `item.category` and updating `item.category` on change
     - Date input (`.housebatch-date-input`, `type="date"`) defaulting to `item.date` and updating `item.date` on change
     - Remove file button (`.btn-remove-housebatch-file`)
   - Updated `submitHouseBatchIngest()` to send each file's individual `item.category`, `item.title`, and `item.date` in `FormData` to `/api/ingest`.
   - Removed obsolete top-level element queries and variable references.
   - Re-exported `detectCategoryFromFilename` to `window` and `module.exports`.
3. **Synchronized ASP.NET Web Assets (`web-net/wwwroot/`)**:
   - Rebuilt `web-net/FileOrganizer.Web.csproj` via `dotnet build`, which automatically copies static assets to `web-net/wwwroot/`.
4. **Automated Test Verification**:
   - **Frontend Vitest (`npm run test:frontend`)**: 60/60 tests passing (added tests for individual category dropdowns/date pickers, keyword matching for `detectCategoryFromFilename`, and individual per-document category/date POST submissions).
   - **Playwright E2E (`.venv/bin/pytest tests/frontend/test_ingest_batch_playwright.py -v`)**: 7/7 tests passing (verified top-level category removal, per-row category rendering, keyword auto-selection, and multi-file distinct category submission to 1 house).
   - **Backend .NET Tests (`~/.dotnet/dotnet test web-net/FileOrganizer.Tests/`)**: 40/40 tests passing.
   - **Backend Pytest (`.venv/bin/pytest tests/test_ingest_api.py -v`)**: 12/12 tests passing.
