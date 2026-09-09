---
slug: 260909-doc-management-move-copy-rename
date: 2026-09-09
description: "Safe UI-based document management: rename, move/copy to folder, move between tenants, and manual permanent lock with sequential folder numbering"
status: complete
---

# Quick Task: Safe Document Management (Rename, Move, Copy, Tenant Reassign & Permanent Lock)

## Objectives

1. **Database Schema & Models**:
   - Add `is_manual INTEGER DEFAULT 0` to `documents` table in `src/db/schema.py` and `src/db/models.py`.
   - Ensure automatic migration in `init_db` if `is_manual` column does not exist.
   - Update `reallocate_house_documents` in `src/db/repository.py` to SKIP any documents where `is_manual = 1` so automated reallocations never overwrite manual assignments.

2. **Sequential Custom Folder Numbering**:
   - Implement helper `get_or_create_numbered_folder(conn, house_id, folder_name)`:
     - Standard folders (01 to 13) retain standard numbering (`01 - بيانات أساسية`, etc.).
     - New custom folders automatically receive the next sequential prefix (e.g., `14 - <Name>`, `15 - <Name>`, etc.) to maintain numeric sorting.

3. **Backend API Endpoints in `src/api/routes.py`**:
   - `PATCH /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}`:
     - Update `arabic_title`, `category` (numbered folder), and `tenant_id` (restricted to same house).
     - Sets `is_manual = 1` and calls `clear_tree_cache()`.
   - `POST /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/copy`:
     - Duplicate document entry in DB with new `vault_id` and `is_manual = 1`.
     - Physically duplicate the PDF slice in `<house_dir>/vault/` (`doc_{new_vault_id}.pdf`).
     - Duplicate `pages` entries for search indexing and call `clear_tree_cache()`.
   - `POST /api/areas/{area_id}/houses/{house_id}/documents/{vault_id}/reset-lock`:
     - Resets `is_manual = 0` so the document can participate in automatic reallocations again.
   - Include `is_manual` in `VaultFileResponse` and timeline responses.

4. **Frontend UI in `src/api/static/index.html`**:
   - Drag & Drop:
     - Draggable document cards to category folder cards (moves folder).
     - Draggable document cards to sidebar tenant items in the same house (moves tenant).
     - Visual drop target highlighting.
   - Document Action Menu (`...`) & Modal:
     - Rename document title.
     - Move to folder (standard 01-13 + existing custom + "+ New Folder" input).
     - Copy to folder (creates independent duplicate).
     - Move to tenant within the house.
     - Reset to automatic.
   - Visual indicator:
     - Small 🔒 badge on manually customized documents.

5. **Testing & Verification**:
   - Comprehensive test suite covering rename, move, copy (with disk file duplication), tenant reassignment, house restriction, sequential folder numbering, and `reallocate_house_documents` permanent lock guarantees.
