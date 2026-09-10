# Quick Task Summary: Batch Copy Documents with Timeline De-duplication

## 1. Overview
- **Feature:** Multi-Select "Copy Selected" (`POST /api/areas/{area}/houses/{house}/documents/batch-copy`) with timeline de-duplication.
- **Problem Solved:** Previously, multi-select operations supported batch move and batch delete, but not batch copy. When copying a document into additional categories for reference, the document should appear in the target category folders while NOT duplicating entries on the timeline.
- **Architectural Solution:**
  - Added `is_timeline_visible INTEGER DEFAULT 1` to `documents` table with automatic column migrations in both Python (`src/db/schema.py`) and .NET (`web-net/Data/DatabaseInitializer.cs`, `web-net/Data/FileOrganizerRepository.cs`).
  - Single copy (`POST .../documents/{vault_id}/copy`) and batch copy (`POST .../documents/batch-copy`) explicitly set `is_timeline_visible = 0` on copies (`is_manual = 1`).
  - Primary/original documents retain `is_timeline_visible = 1`.
  - Timeline queries in FastAPI (`src/api/routes.py:list_timeline`) and ASP.NET Core (`web-net/Data/FileOrganizerRepository.cs:GetTimelineAsync`) filter with `(d.is_timeline_visible IS NULL OR d.is_timeline_visible = 1)`.
  - Category views continue to query all documents, properly displaying the copied document in its target folder.
  - Zero UI checkbox or toggle was added (strictly following requirement: copying always sets `is_timeline_visible = 0`).

---

## 2. Key Changes by Component

### Database Layer
- `src/db/schema.py`:
  - Added `is_timeline_visible INTEGER DEFAULT 1` to table DDL.
  - Added migration in `init_db(conn)` to safely alter existing tables missing the column.
- `src/db/models.py`:
  - Added `is_timeline_visible: int = 1` to `Document` model.
- `src/db/repository.py`:
  - Updated `add_document` to insert `is_timeline_visible`.
  - Updated `copy_document` to set `is_timeline_visible: int = 0` by default.
  - Implemented `batch_copy_documents` copying physical PDF files to `{areas_root}/{area_id}/{house_id}/vault/doc_{new_vid}.pdf`, creating new document records with `is_timeline_visible = 0`, and exposed on `Repository` wrapper.
  - Updated `get_document_metadata` to include `is_timeline_visible`.
- `src/db/__init__.py`:
  - Exported `batch_copy_documents`.
- `web-net/Models/Document.cs`:
  - Added `public int IsTimelineVisible { get; set; } = 1;`.
- `web-net/Models/DTOs.cs`:
  - Added `IsTimelineVisible` to `TimelineItemDto`, `VaultFileDto`, `DocumentMetadataDto`.
  - Added `BatchCopyRequestDto` (`VaultIds`, `TargetCategory`) and `BatchCopyResponseDto` (`Status`, `CopiedCount`, `TargetCategory`, `CopiedVaultIds`).
- `web-net/Data/DatabaseInitializer.cs`:
  - Added `is_timeline_visible INTEGER DEFAULT 1` to schema DDL.
  - Added column check and `ALTER TABLE documents ADD COLUMN is_timeline_visible INTEGER DEFAULT 1` migration.
- `web-net/Data/IFileOrganizerRepository.cs` & `web-net/Data/FileOrganizerRepository.cs`:
  - Added `BatchCopyDocumentsAsync` implementation with physical PDF duplication and fallback to batch file.
  - Updated `CopyDocumentAsync` to set `is_timeline_visible = 0`.
  - Updated `GetTimelineAsync` to filter `(d.is_timeline_visible IS NULL OR d.is_timeline_visible = 1)`.
  - Updated `GetDocumentByVaultIdAsync` to support fallback to batch files for copied documents.

### Backend Endpoints
- **FastAPI (`src/api/routes.py`, `src/api/models.py`):**
  - Added `BatchCopyRequest` and `BatchCopyResponse` Pydantic models.
  - Implemented `POST /api/areas/{area_id}/houses/{house_id}/documents/batch-copy`.
  - Updated `list_timeline` to filter `(d.is_timeline_visible IS NULL OR d.is_timeline_visible = 1)`.
- **ASP.NET Core 8 (`web-net/Program.cs`):**
  - Mapped `POST /api/areas/{areaId}/houses/{houseId}/documents/batch-copy` calling `repo.BatchCopyDocumentsAsync`.

### Frontend & Static Assets
- `src/api/static/index.html` & `web-net/wwwroot/index.html`:
  - Added `#btn-batch-copy` (📋 نسخ المحدد / Copy Selected) in `#batch-action-bar`.
  - Added `#batch-copy-modal` with category select dropdown, custom folder support, and clarifying notice callout: `💡 ملاحظة: النسخ يتيح ظهور الوثائق في مجلد إضافي للرجوع السريع دون تكرارها في الخط الزمني`.
- `src/api/static/js/categories-view.js` & `web-net/wwwroot/js/categories-view.js`:
  - Implemented `openBatchCopyModal`, `closeBatchCopyModal`, and `handleBatchCopySubmit`.
  - Wired `#btn-batch-copy`, `#batch-copy-close`, `#btn-batch-copy-cancel`, `#btn-batch-copy-confirm` in `initBatchOperations`.
  - Exported methods on `window` and `module.exports`.
  - Verified 0 diff between `src/api/static/` and `web-net/wwwroot/`.

---

## 3. Verification & Test Coverage
- **Python Pytest:**
  - `tests/test_v14_features.py`: Added `test_single_document_copy_excluded_from_timeline` and `test_batch_copy_documents_excluded_from_timeline` (All 13 passed).
  - `tests/test_document_management_api.py`: All 13 passed.
- **.NET xUnit:**
  - `web-net/FileOrganizer.Tests/ApiEndpointTests.cs`: Added `BatchCopy_CreatesDocumentCopies_ExcludedFromTimeline` verifying batch copy creation, category presence, and timeline absence.
  - All 51 xUnit tests passed (`Passed! - Failed: 0, Passed: 51`).
- **Vitest Frontend:**
  - `tests/frontend/components/batch_operations.test.js`: Added DOM fixtures and 3 test cases for batch copy modal opening, POST submission, target category validation, and custom folder creation.
  - All 101 Vitest tests passed across all 9 test suites.
