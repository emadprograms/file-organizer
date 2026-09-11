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
  - Generously sized input field (`text-sm font-medium`, `px-3 py-1.5`, ~34px height, `border-2 border-blue-500 rounded-lg shadow-sm`) with `dir="auto"` for bidirectional Arabic/English text alignment.
  - Title container spans and headings equipped with `flex-1 min-w-0`, allowing the rename input to expand across the full available row width rather than collapsing to short title lengths.
  - Display constraints (`truncate` in Categories view, `line-clamp-2` in Timeline view) dynamically unclasped during active editing to prevent input clipping/distortion and restored upon commit or cancellation.
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
- [x] **QCK-08**: Batch Tenant Selection in Move/Copy Modals & Remove Copy Note:
  - **Copy Modal Note Removal**: Removed the amber note block (`💡 ملاحظة: النسخ يتيح ظهور الوثائق في مجلد إضافي للرجوع السريع دون تكرارها في الخط الزمني`) from `#batch-copy-modal` without replacement, streamlining modal simplicity.
  - **Target Tenant Selector**: Added tenant selection dropdown (`المستأجر • Target Tenant`) to both Move Selected (`#batch-move-tenant-select`) and Copy Selected (`#batch-copy-tenant-select`) modals, defaulting to `🏛️ المستأجر الحالي للوثيقة • Same Tenant` (empty value, preserving existing tenancy).
  - **Modal Button Polish**: Cleaned confirm button labels to `Move Documents` and `Copy Documents`.
  - **Dynamic Tenant Population**: `populateBatchTenantSelect` queries active house tenants from `/api/areas/{area}/houses/{house}/tenants` with active indicator (`🟢 ` active vs `👤 ` past) and lease year tags, gracefully falling back to distinct tenants in `currentCategories` in static or offline scenarios.
  - **Dual-Backend Support**: Added `target_tenant_id: Optional[int] = None` to `BatchMoveRequest` / `BatchCopyRequest` in FastAPI and `BatchMoveRequestDto` / `BatchCopyRequestDto` in ASP.NET Core; updates `tenant_id` when supplied and preserves existing tenancy when omitted; batch copy sets duplicate document's `tenant_id = target_tenant_id ?? src.tenant_id`.
- [x] **QCK-09**: Document 3-Dots Dropdown Action Menu & Folders Section Document Date Badge:
  - **Floating Context Menu**: Replaced heavy `#doc-action-modal` on 3-dots button click (`.doc-menu-btn`) with a compact, floating context menu (`.doc-dropdown-menu`) anchored to the trigger button with boundary clamping and Escape / outside-click dismissal.
  - **Action Item Suite**: 5 direct action buttons: Rename Document (triggers inline rename), Move Document (`openBatchMoveForDoc`), Copy Document (`openBatchCopyForDoc`), Show in Timeline, and Delete Document (`handleDeleteSingleDoc`).
  - **Timeline Navigation**: "Show in Timeline" action switches active tab to Timeline, clears any conflicting tenant filter, smoothly scrolls the target document card to center viewport, and pulses blue highlight (`ring-4 ring-blue-500 bg-blue-50`).
  - **Folders Section Document Date Badge**: Always-visible document date badge with light gray background (`doc-date-badge bg-slate-100 text-slate-500 text-[10px] font-mono`) rendered directly before the 3-dots button in the Folders / Categories section (`categories-view.js`), showing document date with fallback to `No Date`.
- [x] **QCK-10**: Category Folder Circular Document Count Badge & Refined Document Date Sizing:
  - **Circular Document Count Badge**: Replaced the verbose `"${cat.document_count} Documents"` pill on folder header cards in `categories-view.js` with a sleek circular count badge (`min-w-[20px] h-5 rounded-full`) rendering just the count number inside a circle, equipped with accessibility tooltip (`title="${count} Documents"`).
  - **Refined Document Date Badge Sizing**: Reduced font size of `.doc-date-badge` on document rows in Categories view to `text-[9px] font-mono tracking-tight`, freeing ~12-15px horizontal width per row to prevent document name truncation while maintaining crisp legibility.
- [x] **QCK-11**: Category-Specific Folder Icons & Empty Folder for Custom Categories:
  - **Descriptive Standard Icons**: Implemented unique, semantic Heroicons outline icons for categories 01 through 13 in Folders view (`FOLDER_ICONS`, `.folder-icon-box`, `getFolderIconSvg`), representing property, tenant profile, allocation, key handover, contracts, utilities, salary deductions, stop deduction, notices, maintenance, inspections, alterations, and letters.
  - **Empty Folder for Custom**: Automatically uses the clean empty folder icon for custom user-created folders (14+).
- [x] **QCK-12**: Replace Folder "Select All" Text Button with Select Checkbox:
  - **Folder Select Checkbox UI**: Replaced `.btn-select-all-folder` button on category cards with `.folder-select-checkbox` positioned right before `.folder-icon-box` (`w-3.5 h-3.5 rounded text-blue-600 focus:ring-blue-500 border-slate-300 cursor-pointer flex-shrink-0`), with visual alignment spacer (`<span class="w-3.5 h-3.5 flex-shrink-0"></span>`) for empty folders.
  - **Reveal and Select Documents**: Clicking the checkbox immediately un-hides the documents list (`docsContainer.classList.remove('hidden')`) and toggles full folder selection.
  - **Reactive Synchronization**: Toggling document checkboxes updates parent folder checkbox to checked, indeterminate, or unchecked. Global select all and deselect all stay fully in sync.
- [x] **VER-07**: Comprehensive multi-stack test suite covering all capabilities across Python and .NET:
  - 84 ASP.NET Core xUnit tests (`web-net/FileOrganizer.Tests/`, including 32 in `ArabicReshaperTests.cs`).
  - 17 Python v14 pytest tests (`tests/test_v14_features.py`).
  - 13 Python document management tests (`tests/test_document_management_api.py`).
  - 143 Frontend Vitest tests across 13 files (`npm run test:frontend`, including 16 in `batch_operations.test.js` and 8 in `folder_select_checkbox.test.js`).
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
| **BAT-01** | Multi-select checkboxes & floating action bar in Category View | Phase 106 | Complete | `src/api/static/js/categories-view.js`, `tests/frontend/components/batch_operations.test.js` (16 tests) |
| **BAT-02** | Batch Move and Batch Delete backend endpoints | Phase 106 | Complete | `tests/test_v14_features.py` (`test_batch_move_documents`, `test_batch_delete_documents`), `ApiEndpointTests.cs` |
| **QCK-02** | Batch Copy & Timeline De-duplication Architecture (`is_timeline_visible`) | Phase 106 / QCK-02 | Complete | `tests/test_v14_features.py` (2 tests), `tests/frontend/components/batch_operations.test.js` (3 copy tests), `ApiEndpointTests.cs` (`BatchCopy_*`) |
| **HSE-01** | House creation backend endpoint and directory scaffold | Phase 107 | Complete | `tests/test_v14_features.py` (`test_create_house_*`), `ApiEndpointTests.cs` (`PostCreateHouse_*`) |
| **HSE-02** | "+ Add House" UI modal and live grid refresh in Area Grid | Phase 107 | Complete | `src/api/static/js/area-grid.js`, `tests/frontend/components/add_house.test.js` (5 tests) |
| **KBD-01** | Global Keyboard Shortcuts Helper modal (`?`) & navbar button | Phase 108 | Complete | `src/api/static/js/keyboard-shortcuts.js`, `tests/frontend/components/keyboard_shortcuts.test.js` (12 tests) |
| **QCK-05** | Double-Click Inline Document Renaming in Categories & Timeline views | Phase 108 / QCK-05 | Complete | `tests/frontend/components/inline_rename.test.js` (7 tests), `src/api/static/js/categories-view.js`, `src/api/static/js/timeline-view.js` |
| **QCK-06** | Relocation of Export Archive button to Document Panel header & removal of bottom archive summary | Phase 105 / QCK-06 | Complete | `tests/frontend/components/house_profile.test.js`, `tests/frontend/components/export_archive_modal.test.js`, `tests/frontend/test_house_register.py` |
| **QCK-07** | Streamline export modal to intuitive visual-first layout & remove emojis from batch buttons | Phase 105 / QCK-07 | Complete | `tests/frontend/components/export_archive_modal.test.js` (5 tests), `tests/frontend/components/batch_operations.test.js` (16 tests), zero static diff |
| **QCK-08** | Batch Tenant Selection in Move/Copy Modals & Remove Copy Note | Phase 106 / QCK-08 | Complete | `tests/frontend/components/batch_operations.test.js` (16 tests), `tests/test_v14_features.py` (`test_batch_move_with_target_tenant`, `test_batch_copy_with_target_tenant`), `ApiEndpointTests.cs`, zero static diff |
| **QCK-09** | Document 3-Dots Dropdown Action Menu & Folders Section Document Date Badge | Phase 108 / QCK-09 | Complete | `tests/frontend/components/doc_dropdown_and_date.test.js` (14 tests), `src/api/static/js/doc-manager.js`, `src/api/static/js/categories-view.js`, `src/api/static/js/timeline-view.js`, zero static diff |
| **QCK-10** | Category Folder Circular Document Count Badge & Refined Document Date Sizing | Phase 108 / QCK-10 | Complete | `tests/frontend/components/doc_dropdown_and_date.test.js` (14 tests), `src/api/static/js/categories-view.js`, zero static diff |
| **QCK-11** | Category-Specific Folder Icons (01-13 descriptive, 14+ empty folder) | Phase 108 / QCK-11 | Complete | `tests/frontend/components/categories_folder_icons.test.js` (6 tests), `src/api/static/js/categories-view.js`, zero static diff |
| **QCK-12** | Replace Folder "Select All" Text Button with Select Checkbox (`.folder-select-checkbox`) that Reveals Documents and Selects All | Phase 106 / QCK-12 | Complete | `tests/frontend/components/folder_select_checkbox.test.js` (8 tests), `tests/frontend/components/batch_operations.test.js` (16 tests), `src/api/static/js/categories-view.js`, zero static diff |
| **VER-07** | Comprehensive multi-stack automated testing suite (Pytest, Vitest, Playwright, xUnit) | Phase 108 | Complete | 305+ automated tests passing across 4 test runners (84 xUnit, 17 v14 pytest, 13 doc management, 143 Vitest across 13 files, 49 Playwright); zero static asset diff. |
