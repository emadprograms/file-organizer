# Requirements: Milestone v14.0 Power-User Operations & Portfolio Expansion

## Milestone v14.0 Goals

Equip the digital archive management system with power-user operational tools: one-click house archive ZIP export, interactive export options modal with combined chronological PDF dossier generation (descending sort, running footer with preserved category numbering, Arabic cursive reshaping and BiDi visual reordering), multi-document batch operations (bulk move, bulk delete, and bulk copy with timeline de-duplication), portfolio expansion with UI-based house creation, an interactive keyboard shortcuts modal (`?`), and complete parity across both FastAPI and ASP.NET Core 8.0 backends with comprehensive test coverage.

## Requirements

### Archive Export & Dossier Generation
- [x] **EXP-01**: Backend ZIP export stream endpoint `GET /api/areas/{area}/houses/{house}/export-zip` in both FastAPI and ASP.NET Core. Packages all vault documents for the requested house into an in-memory or streamed ZIP archive with clean, collision-free Arabic filenames (`{folder_index}_{title}.pdf`), setting proper `Content-Disposition` attachment headers and normalizing folder prefixes via `FOLDER_PREFIXES`.
- [x] **EXP-02**: Modern UI Export Button on the House Profile header (`[ 📦 Export Archive ZIP ]`). Displays an active download spinner during generation, handles browser file download, and provides user feedback via toast notifications.
- [x] **QCK-01**: Interactive Export Options Modal (`#export-archive-modal`) & Combined Chronological PDF Dossier (`GET /api/areas/{area}/houses/{house}/export-pdf`):
  - **Export Format Selection**: Format Card A (Categorized ZIP Archive) vs Format Card B (Combined Chronological PDF Dossier).
  - **Tenancy Scope Filter**: Full House Record (`All Tenants`) vs Individual active/past tenant from `profile.tenants`.
  - **Standard 2-Digit Folder Numbering**: Normalizes folder names with `FOLDER_PREFIXES` so every folder in the ZIP has its canonical prefix (`01 - `, `05 - `, `06 - `, etc.).
  - **PDF Dossier Generation**: Merges physical vault PDFs into a single continuous PDF document across Python (PyMuPDF `fitz`) and .NET (`PdfSharpCore`).
- [x] **QCK-03**: Minimalist 3-Column Running Footer & Descending Chronological Sort for PDF Dossier:
  - **Descending Chronological Sort**: Orders documents newest-first (Page 1 contains the most recent document, followed by older documents, with undated documents placed at the end).
  - **Minimalist 3-Column Running Footer**: Rendered on every page of the generated PDF dossier:
    - Bottom-Left: Document primary filing date (`YYYY-MM-DD`), blank if undated.
    - Bottom-Center: Category name with number prefix preserved (e.g. `05 - عقود`, `06 - كهرباء وماء`).
    - Bottom-Right: Group & Master pagination `X/Y  (Z)` (e.g. `1/3  (14)`).
    - Typography & Margins: 7.5 pt muted slate gray (`#64748b`), 16 pt margin. Zero verbose labels (no "Date:", "Category:", "Page:").
- [x] **QCK-04**: Arabic Cursive Text Shaping & BiDi Visual Reordering in PDF Export Running Footer:
  - **Python FastAPI Backend** (`src/api/routes.py`): Utilizes `arabic-reshaper` and `python-bidi` (`get_display(arabic_reshaper.reshape(cat))`) to eliminate disconnected "terminal Arabic" isolated characters and accurately compute shaped text width for center alignment.
  - **ASP.NET Core 8.0 Backend** (`web-net/Common/ArabicReshaper.cs` & `web-net/Program.cs`): Zero-dependency pure C# `ArabicReshaper.ReshapeAndReorder` mapping standard Arabic characters (`\u0600`–`\u06FF`) to Unicode Presentation Forms-B (`\uFE80`–`\uFEFC`), supporting dual-joining, right-joining, and Lam-Alef ligatures (`لا`, `لأ`, `لإ`, `لآ`), reversing RTL Arabic runs while preserving LTR numeric tokens (`05 - `) and mirroring bracket punctuation.

### Multi-Select Batch Document Operations
- [x] **BAT-01**: Multi-select checkbox UI in category folder document lists. Features per-card selection checkboxes, a folder-level toggle, and a global "Select All / Deselect All" toggle. Displays a glassmorphism dark floating action dock (`#batch-action-bar`) with dynamic selection counter and action buttons (`[ Move Selected ]`, `[ Copy Selected ]`, `[ Delete Selected ]`, `[ Deselect ]`).
- [x] **BAT-02**: Batch Move and Batch Delete backend endpoints in both FastAPI and ASP.NET Core:
  - `POST /api/areas/{area}/houses/{house}/documents/batch-delete`: Cascade deletion of selected vault documents from SQLite database and filesystem storage with confirmation modal.
  - `POST /api/areas/{area}/houses/{house}/documents/batch-move`: Move selected documents to a target category folder in a single atomic transaction.
- [x] **QCK-02**: Multi-Select Batch Copy & Timeline De-duplication Architecture:
  - `POST /api/areas/{area}/houses/{house}/documents/batch-copy`: Duplicates document references into an additional category folder for fast reference.
  - **Database Schema Migration**: Added `is_timeline_visible INTEGER DEFAULT 1` to `documents` table with automatic column migrations in SQLite and Dapper.
  - **Timeline De-duplication**: Copied documents are stored with `is_timeline_visible = 0`. Timeline queries in FastAPI and ASP.NET Core filter `(d.is_timeline_visible IS NULL OR d.is_timeline_visible = 1)` so each physical real-world event is represented exactly once without clutter.
  - **Category View Transparency**: Copied documents appear normally in target category folders.
  - **Unified Single Copy**: Single document 3-dot Copy (`POST .../documents/{vault_id}/copy`) also unified with `is_timeline_visible = 0`.
  - **Storage Efficiency**: Physical vault stores 1 physical file without wasteful duplicate storage.

### Portfolio Expansion
- [x] **HSE-01**: House creation backend endpoint `POST /api/areas/{area}/houses` in both FastAPI and ASP.NET Core. Registers the house in SQLite, optionally creates the initial active tenant, validates conflicts (409 on duplicates), and initializes the physical filesystem directory scaffold (`{area}/{house}/batches/` and `{area}/{house}/vault/`).
- [x] **HSE-02**: "+ Add House" UI trigger and modal (`#add-house-modal`) in the Area Grid. Allows property managers to select an Area, input House Number/Name, and optionally add an initial tenant. Dynamically refreshes the house grid upon creation without page reload.

### Keyboard Shortcuts & Verification
- [x] **KBD-01**: Global Keyboard Shortcuts Helper Modal (`?`). Pressing `?` (Shift+/) opens a clean modal listing all available keyboard shortcuts (`⌘K` Search, `⌘I` Ingest, `Space` Quick Look, `Esc` Close, `?` Shortcuts). Includes a subtle navbar trigger button (`#btn-shortcuts-trigger`), backdrop dismissal, and input/textarea typing suppression guards.
- [x] **QCK-05**: Double-Click Inline Document Renaming in Categories and Timeline views:
  - Double-clicking document title text in either Categories folder list (`span.doc-title-text`) or Timeline view (`h4.doc-title-text`) transforms title into an inline text input pre-filled with the original title.
  - Event isolation on input (`click`, `dblclick`, `mousedown`, `dragstart`, `keydown`) prevents accidental card selection, card-click open trigger, or dragging while editing.
  - Keyboard shortcuts & blur: `Enter` to commit, `Escape` to cancel and revert without network request, and `blur` to commit or revert.
  - Submits `PATCH /api/areas/{area}/houses/{house}/documents/{vault_id}` with `{ "arabic_title": newTitle }`, updates in-memory document state, updates DOM, and provides success/error toast notifications.
  - Empty or unchanged input reverts without sending network requests.
- [x] **QCK-06**: Relocation of Export House Archive Button to Document Panel Header & Removal of Bottom Archive Summary Box:
  - **Archive Box Removal**: Removed redundant and confusing `archiveBox` (`بيانات الأرشيف الرقمي للمنزل`) from the bottom of House Profile, eliminating bottom clutter and focusing exclusively on the Tenancy Register and tenant cards.
  - **Header Export Button**: Pinned `#btn-export-house-archive` to the top Document Panel header adjacent to `#btn-manage-tenants` for 0-scroll permanent visibility across Profile, Folders, and Timeline views.
  - **Backward Compatibility**: Full compatibility fallback for legacy `#btn-export-house-zip`.
- [x] **QCK-07**: Streamline House Archive Export Options Modal & Remove Batch Button Emojis:
  - **Export Modal Streamlining**: Replaced verbose explanatory paragraphs with intuitive visual design in `#export-archive-modal`. Streamlined header title (`تصدير الأرشيف • Export Archive`) without subtitle paragraph; visual format cards (Card A: `📦 ZIP` with `مجلدات • Folders`; Card B: `📄 PDF` with `تسلسل زمني • Timeline`) without long descriptive paragraphs; streamlined tenant scope (`المستأجر • Tenant`) with default option `🏛️ كامل السجل • All Records`; footer buttons (`Cancel` and `⬇️ Download`).
  - **Batch Bar Emojis Removal**: Removed distracting emojis (`📁`, `📋`, `🗑️`) from Move, Copy, and Delete buttons while preserving the `✕` icon on `#btn-batch-deselect` (`<span>✕</span><span>Deselect</span>`).
- [x] **VER-07**: Comprehensive multi-stack test suite covering all capabilities across Python and .NET:
  - 84 ASP.NET Core xUnit tests (`web-net/FileOrganizer.Tests/`, including 32 in `ArabicReshaperTests.cs`).
  - 15 Python v14 pytest tests (`tests/test_v14_features.py`).
  - 13 Python document management tests (`tests/test_document_management_api.py`).
  - 109 Frontend Vitest tests across 10 files (`npm run test:frontend`).
  - 49 Playwright E2E tests.
  - Zero static asset diff between `src/api/static/` and `web-net/wwwroot/`.

## Traceability

| Requirement | Description | Phase / Refinement | Status | Verification Evidence |
|---|---|---|---|---|
| **EXP-01** | Backend ZIP export stream endpoint in FastAPI & ASP.NET Core | Phase 105 | Complete | `tests/test_v14_features.py` (`test_export_house_archive_zip`), `ApiEndpointTests.cs` (`ExportZip_ReturnsZipArchive`) |
| **EXP-02** | UI Export Archive ZIP button on House Profile header | Phase 105 | Complete | `src/api/static/js/house-profile.js`, `tests/frontend/components/house_profile.test.js` |
| **QCK-01** | Interactive Export Options Modal & Chronological PDF Dossier Pipeline | Phase 105 / QCK-01 | Complete | `tests/frontend/components/export_archive_modal.test.js` (5 tests), `tests/test_v14_features.py`, `ApiEndpointTests.cs` |
| **QCK-03** | Descending Chronological Dossier Sort & Minimalist 3-Column Running Footer with Preserved Numbers | Phase 105 / QCK-03 | Complete | `tests/test_v14_features.py` (`test_export_house_archive_pdf_descending_chronological_order`), `ApiEndpointTests.cs` (`ExportPdf_ReturnsChronologicalMergedPdf`) |
| **QCK-04** | Arabic Cursive Text Shaping & BiDi Visual Reordering in Running Footer | Phase 105 / QCK-04 | Complete | `tests/test_v14_features.py` (`test_export_house_archive_pdf_running_footer`), `web-net/FileOrganizer.Tests/ArabicReshaperTests.cs` (32 tests) |
| **BAT-01** | Multi-select checkboxes & floating action bar in Category View | Phase 106 | Complete | `src/api/static/js/categories-view.js`, `tests/frontend/components/batch_operations.test.js` (10 tests) |
| **BAT-02** | Batch Move and Batch Delete backend endpoints | Phase 106 | Complete | `tests/test_v14_features.py` (`test_batch_move_documents`, `test_batch_delete_documents`), `ApiEndpointTests.cs` |
| **QCK-02** | Batch Copy & Timeline De-duplication Architecture (`is_timeline_visible`) | Phase 106 / QCK-02 | Complete | `tests/test_v14_features.py` (2 tests), `tests/frontend/components/batch_operations.test.js` (3 copy tests), `ApiEndpointTests.cs` (`BatchCopy_*`) |
| **HSE-01** | House creation backend endpoint and directory scaffold | Phase 107 | Complete | `tests/test_v14_features.py` (`test_create_house_*`), `ApiEndpointTests.cs` (`PostCreateHouse_*`) |
| **HSE-02** | "+ Add House" UI modal and live grid refresh in Area Grid | Phase 107 | Complete | `src/api/static/js/area-grid.js`, `tests/frontend/components/add_house.test.js` (5 tests) |
| **KBD-01** | Global Keyboard Shortcuts Helper modal (`?`) & navbar button | Phase 108 | Complete | `src/api/static/js/keyboard-shortcuts.js`, `tests/frontend/components/keyboard_shortcuts.test.js` (12 tests) |
| **QCK-05** | Double-Click Inline Document Renaming in Categories & Timeline views | Phase 108 / QCK-05 | Complete | `tests/frontend/components/inline_rename.test.js` (7 tests), `src/api/static/js/categories-view.js`, `src/api/static/js/timeline-view.js` |
| **QCK-06** | Relocation of Export Archive button to Document Panel header & removal of bottom archive summary | Phase 105 / QCK-06 | Complete | `tests/frontend/components/house_profile.test.js`, `tests/frontend/components/export_archive_modal.test.js`, `tests/frontend/test_house_register.py` |
| **QCK-07** | Streamline export modal to intuitive visual-first layout & remove emojis from batch buttons | Phase 105 / QCK-07 | Complete | `tests/frontend/components/export_archive_modal.test.js` (5 tests), `tests/frontend/components/batch_operations.test.js` (10 tests), zero static diff |
| **VER-07** | Comprehensive multi-stack automated testing suite (Pytest, Vitest, Playwright, xUnit) | Phase 108 | Complete | 270+ automated tests passing across 4 test runners (84 xUnit, 15 v14 pytest, 13 doc management, 109 Vitest, 49 Playwright); zero static asset diff. |
