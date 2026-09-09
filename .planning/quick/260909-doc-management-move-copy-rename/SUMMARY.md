# Quick Task Summary: Safe UI-Based Document Management

**Slug:** `260909-doc-management-move-copy-rename`  
**Date:** 2026-09-09  
**Status:** Completed  

---

## 1. Executive Summary

Empowered users to safely manage documents directly from the web interface without touching raw database tables:
- **Rename Arabic Document Title**: Inline and via action modal.
- **Move to Category Folder**: Drag-and-drop or modal selector supporting standard folders (`01`–`13`) and dynamic custom folders (`14+`).
- **Copy / Duplicate to Folder**: Independent PDF duplication in the on-disk vault and independent database record creation.
- **Move to Tenant**: Strict same-house isolation (rejecting cross-house tenant reassignment with HTTP 400).
- **Permanent Manual Lock (`is_manual = 1`)**: Ensures automated tenant document reallocations (`reallocate_house_documents`) never overwrite manual user adjustments.
- **Reset to Automatic**: One-click unlock (`is_manual = 0`) restoring automated reallocation eligibility.

---

## 2. Key Architecture & Design Decisions

### 2.1 Schema & Migrations
- Added `is_manual INTEGER DEFAULT 0` and index `idx_documents_manual` to `documents` table in `src/db/schema.py`.
- Added automatic non-destructive column migration in `init_db(conn)` using SQLite `PRAGMA table_info(documents)`.
- Updated `Document` dataclass in `src/db/models.py`.

### 2.2 Reallocation Safety Shield
- In `src/db/repository.py`, `reallocate_house_documents` query was updated to:
  ```sql
  SELECT vault_id, document_type, date, category, raw_ocr_text, tenant_id, is_manual
  FROM documents
  WHERE house_id = ? AND (is_manual IS NULL OR is_manual = 0)
  ```
  Any document touched manually receives `is_manual = 1` and is completely shielded from algorithmic tenant reassignment during house tenant additions or configuration updates.

### 2.3 Sequential Numbered Folders (`14+`)
- Created `get_or_create_numbered_folder(conn, house_id, folder_name)`:
  - If target folder is already a standard folder (`01` through `13`), preserves canonical name.
  - If target is a custom folder name without a prefix, scans existing categories in the house for maximum prefix number (minimum 13) and assigns the next sequential number (e.g. `14 - تقارير البلدية`, `15 - إيصالات خاصة`).
  - Ensures natural sorting `{ numeric: true }` in JavaScript timeline and category views.

### 2.4 Document Copying vs Physical Slices
- `copy_document(conn, vault_id, target_category, new_tenant_id)` generates a new `vault_id` in `documents`.
- Physically copies `house_dir / "vault" / f"doc_{vault_id}.pdf"` to `f"doc_{new_vault_id}.pdf"` via `shutil.copy2`.
- Preserves relational integrity while avoiding unique constraint violations on `pages(batch_id, page_number)`.

---

## 3. Backend API Endpoints

- `PATCH /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}`:
  - Updates `arabic_title`, `category`, and `tenant_id`.
  - Enforces same-house validation for `tenant_id`.
  - Sets `is_manual = 1` and clears memory caches (`clear_tree_cache()`).
- `POST /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/copy`:
  - Duplicates document record and disk file, assigning target category and setting `is_manual = 1`.
- `POST /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/reset-lock`:
  - Resets `is_manual = 0` and triggers `reallocate_house_documents` to recalculate tenant placement.
- `GET /api/areas/{area_id}/houses/{house_id}/vault`, `/timeline`, `/categories`:
  - Enriched with `tenant_id`, `category`, and `is_manual` fields.

---

## 4. Frontend Experience (`src/api/static/index.html`)

- **Interactive Drag & Drop**:
  - Drag document cards onto category folder cards to instantly recategorize.
  - Drag document cards onto sidebar tenant buttons to reassign tenants within the house.
  - Clear drop target visual highlights and toast feedback.
- **Document Management Modal (`...`)**:
  - Accessible from both Timeline and Category views.
  - Actions: Edit Arabic Title, Move Folder (standard + custom), Copy Folder (with duplicate slice), Change Tenant, and Reset to Automatic.
- **Visual Status Badges**:
  - `🔒` lock icon displayed next to documents with `is_manual = 1` indicating user protection.

---

## 5. Verification & Tests

- **Test Suite**: `tests/test_document_management_api.py` (7 comprehensive tests):
  - `test_rename_document_arabic_title`: Verified title update and manual lock flag.
  - `test_move_document_category_sequential_numbering`: Verified sequential folder numbering (`14`, `15`).
  - `test_reassign_document_tenant_same_house`: Verified valid tenant move within house.
  - `test_reassign_document_tenant_different_house_rejected`: Verified 400 Bad Request on cross-house attempt.
  - `test_reallocation_ignores_manual_locked_documents`: Verified algorithmic reallocation skips locked docs.
  - `test_reset_manual_lock`: Verified unlock and subsequent reallocation.
  - `test_copy_document_creates_duplicate_and_file`: Verified DB duplication and physical PDF file creation on disk.
- **Regression Testing**: All existing API and repository tests passed (24/24 passing in under 1s).
